#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import os
import sys
from ansible.module_utils import distro
from ansible.module_utils.basic import AnsibleModule


class OpenVPN(object):
    """
    Main Class to implement the Icinga2 API Client
    """
    module = None

    def __init__(self, module):
        """
          Initialize all needed Variables
        """
        self.module = module

        self.state = module.params.get("state")
        self.force = module.params.get("force", False)
        self._secret = module.params.get('secret', None)
        self._username = module.params.get('username', None)

        self._chdir = module.params.get('chdir', None)
        self._creates = module.params.get('creates', None)
        self._destination_directory = module.params.get('destination_directory', None)

        self._openvpn = module.get_bin_path('openvpn', True)
        self._easyrsa = module.get_bin_path('easyrsa', True)

        (self.distribution, self.version, self.codename) = distro.linux_distribution(full_distribution_name=False)

    def run(self):
        """
          runner
        """
        result = dict(
            failed=False,
            changed=False,
            ansible_module_results="none"
        )

        if self._chdir:
            os.chdir(self._chdir)

        if self.force and self._creates:
            self.module.log(msg="force mode ...")
            if os.path.exists(self._creates):
                self.module.log(msg="remove {}".format(self._creates))
                os.remove(self._creates)

        if self._creates:
            if os.path.exists(self._creates):
                message = "nothing to do."
                if self.state == "genkey":
                    message = "tls-auth key already created"

                return dict(
                    changed=False,
                    message=message
                )

        args = []

        if self.state == "genkey":
            args.append(self._openvpn)
            args.append("--genkey")
            if self.distribution.lower() == "ubuntu" and self.version == "20.04":
                # OpenVPN 2.5.5
                # ubuntu 20.04 wants `--secret`
                args.append("--secret")
            else:
                # WARNING: Using --genkey --secret filename is DEPRECATED.  Use --genkey secret filename instead.
                args.append("secret")
            args.append(self._secret)

        if self.state == "create_user":
            return self.__create_vpn_user()
            # args.append(self._easyrsa)
            # args.append("--batch")
            # args.append("build-client-full")
            # args.append(self._username)
            # args.append("nopass")

        rc, out = self._exec(args)

        result['result'] = "{}".format(out.rstrip())

        if rc == 0:
            force_mode = "0600"
            if isinstance(force_mode, str):
                mode = int(force_mode, base=8)

            os.chmod(self._secret, mode)

            result['changed'] = True
        else:
            result['failed'] = True

        return result

    def __create_vpn_user(self):
        """
        """
        result = dict(
            failed=True,
            changed=False,
            ansible_module_results="none"
        )
        message = "init function"

        cert_exists = self.__vpn_user_req()

        if cert_exists:
            return dict(
                failed=False,
                changed=False,
                message="cert req for user {} exists".format(self._username)
            )

        args = []

        # rc = 0
        args.append(self._easyrsa)
        args.append("--batch")
        args.append("build-client-full")
        args.append(self._username)
        args.append("nopass")

        rc, out = self._exec(args)

        result['result'] = "{}".format(out.rstrip())

        if rc == 0:
            """
            """
            # read key file
            key_file = os.path.join("pki", "private", "{}.key".format(self._username))
            cert_file = os.path.join("pki", "issued", "{}.crt".format(self._username))

            self.module.log(msg="  key_file : '{}'".format(key_file))
            self.module.log(msg="  cert_file: '{}'".format(cert_file))

            if os.path.exists(key_file) and os.path.exists(cert_file):
                """
                """
                with open(key_file, "r") as k_file:
                    k_data = k_file.read().rstrip('\n')

                cert = self.extract_certs_as_strings(cert_file)[0].rstrip('\n')

                # take openvpn client template and fill
                from jinja2 import Template

                tpl = "/etc/openvpn/client.ovpn.template"

                with open(tpl) as file_:
                    tm = Template(file_.read())
                # self.module.log(msg=json.dumps(data, sort_keys=True))

                d = tm.render(
                    key=k_data,
                    cert=cert
                )

                destination = os.path.join(self._destination_directory, "{}.ovpn".format(self._username))

                with open(destination, "w") as fp:
                    fp.write(d)

                force_mode = "0600"
                if isinstance(force_mode, str):
                    mode = int(force_mode, base=8)

                os.chmod(destination, mode)

                result['failed'] = False
                result['changed'] = True
                message = "ovpn file successful written as {}".format(destination)

            else:
                result['failed'] = True
                message = "can not find key or certfile for user {}".format(self._username)

        result['result'] = message

        return result

    def extract_certs_as_strings(self, cert_file):
        certs = []
        with open(cert_file) as whole_cert:
            cert_started = False
            content = ''
            for line in whole_cert:
                if '-----BEGIN CERTIFICATE-----' in line:
                    if not cert_started:
                        content += line
                        cert_started = True
                    else:
                        print('Error, start cert found but already started')
                        sys.exit(1)
                elif '-----END CERTIFICATE-----' in line:
                    if cert_started:
                        content += line
                        certs.append(content)
                        content = ''
                        cert_started = False
                    else:
                        print('Error, cert end found without start')
                        sys.exit(1)
                elif cert_started:
                    content += line

            if cert_started:
                print('The file is corrupted')
                sys.exit(1)

        return certs

    def __vpn_user_req(self):
        """
        """
        req_file = os.path.join("pki", "reqs", "{}.req".format(self._username))

        if os.path.exists(req_file):
            return True

        return False

    def _exec(self, commands):
        """
          execute shell program
        """
        rc, out, err = self.module.run_command(commands, check_rc=True)

        if int(rc) != 0:
            self.module.log(msg=f"  rc : '{rc}'")
            self.module.log(msg=f"  out: '{out}'")
            self.module.log(msg=f"  err: '{err}'")

        return rc, out


# ===========================================
# Module execution.
#


def main():

    args = dict(
        state=dict(
            default="genkey",
            choices=["genkey", "create_user"]
        ),
        force=dict(
            required=False,
            default=False,
            type="bool"
        ),
        secret=dict(
            required=True,
            type="str"
        ),
        username=dict(
            required=False,
            type="str"
        ),
        easyrsa_directory=dict(
            required=False,
            type="str"
        ),
        destination_directory=dict(
            required=False,
            type="str"
        ),
        chdir=dict(
            required=False
        ),
        creates=dict(
            required=False
        ),
    )
    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=False,
    )

    o = OpenVPN(module)
    result = o.run()

    module.log(msg="= result: {}".format(result))

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
