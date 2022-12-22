# coding: utf-8
from __future__ import unicode_literals

from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

import json
import pytest
import os

import testinfra.utils.ansible_runner

HOST = 'server'

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts(HOST)


def pp_json(json_thing, sort=True, indents=2):
    if type(json_thing) is str:
        print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
    else:
        print(json.dumps(json_thing, sort_keys=sort, indent=indents))
    return None


def base_directory():
    """ ... """
    cwd = os.getcwd()

    if ('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


def read_ansible_yaml(file_name, role_name):
    ext_arr = ["yml", "yaml"]

    read_file = None

    for e in ext_arr:
        test_file = "{}.{}".format(file_name, e)
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return "file={} name={}".format(read_file, role_name)


def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - vars/${DISTRIBUTION}.yaml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution
    operation_system = None

    if distribution in ['debian', 'ubuntu']:
        operation_system = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        operation_system = "redhat"
    elif distribution in ['arch', 'artix']:
        operation_system = f"{distribution}linux"

    file_defaults = f"file={base_dir}/defaults/main.yml name=role_defaults"
    file_vars = f"file={base_dir}/vars/main.yml name=role_vars"
    file_molecule = f"file={molecule_dir}/group_vars/all/vars.yml name=test_vars"
    file_distibution = f"file={base_dir}/vars/{operation_system}.yml name=role_distibution"
    # file_host_molecule = read_ansible_yaml("{}/host_vars/{}/vars".format(base_dir, HOST), "host_vars")

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distribution_vars = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distribution_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_files(host, get_vars):
    """
    """
    files = [
        "/etc/openvpn/server/server.conf",
        "/etc/openvpn/keys/server/ca.crt",
        "/etc/openvpn/keys/server/dh2048.pem",
        "/etc/openvpn/keys/server/server.crt",
        "/etc/openvpn/keys/server/server.key",
        "/etc/openvpn/keys/server/ta.key",
        "/etc/openvpn/client.ovpn.template"
    ]

    for file in files:
        f = host.file(file)
        assert f.exists
        assert f.is_file


def test_user(host, get_vars):
    """
    """
    _defaults = get_vars.get("openvpn_defaults_server")
    _configure = get_vars.get("openvpn_server")

    if _defaults and _configure:
        data = merge_two_dicts(_defaults, _configure)
    else:
        data = _defaults

    user = data.get("user")
    group = data.get("group")

    print(f"user  : {user}")
    print(f"group : {group}")

    assert host.group(group).exists
    assert host.user(user).exists


def test_service(host, get_vars):
    """
    """
    distribution = host.system_info.distribution

    service = host.service(
        get_vars.get("openvpn_service_name")
    )

    if distribution == 'artix':
        service = host.service("openvpn")

    print(f"service: {service}")

    assert service.is_enabled
    assert service.is_running


def test_open_port(host, get_vars):
    """
    """
    listening = host.socket.get_listening_sockets()
    interfaces = host.interface.names()
    eth = []

    if "eth0" in interfaces:
        eth = host.interface("eth0").addresses

    for i in listening:
        print(i)

    for i in interfaces:
        print(i)

    for i in eth:
        print(i)

    _defaults = get_vars.get("openvpn_defaults_server")
    _configure = get_vars.get("openvpn_server")
    data = merge_two_dicts(_defaults, _configure)

    port = data.get("port")

    service = host.socket("udp://{0}:{1}".format("0.0.0.0", port))
    assert service.is_listening
