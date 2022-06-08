#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import os
import sys
import hashlib

from ansible.module_utils.basic import AnsibleModule


class OpenVPNOvpn(object):
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
        self._username = module.params.get('username', None)
        self._destination_directory = module.params.get('destination_directory', None)

        self._chdir = module.params.get('chdir', None)
        self._creates = module.params.get('creates', None)

        self._openvpn = module.get_bin_path('openvpn', True)
        self._easyrsa = module.get_bin_path('easyrsa', True)

        self.key_file = os.path.join("pki", "private", f"{self._username}.key")
        self.crt_file = os.path.join("pki", "issued", f"{self._username}.crt")
        self.dst_file = os.path.join(self._destination_directory, f"{self._username}.ovpn")

        self.dst_checksum_file = os.path.join(self._destination_directory, f".{self._username}.ovpn.sha256")

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

        self.__validate_checksums()

        if self.force:
            self.module.log(msg="force mode ...")
            if os.path.exists(self.dst_file):
                self.module.log(msg=f"remove {self.dst_file}")
                os.remove(self.dst_file)
                os.remove(self.dst_checksum_file)

        if self._creates:
            if os.path.exists(self._creates):
                message = "nothing to do."
                if self.state == "present":
                    message = "user req already created"

                return dict(
                    changed=False,
                    message=message
                )

        if self.state == "present":
            return self.__create_ovpn_config()
        if self.state == "absent":
            return self.__remove_ovpn_config()

        return result

    def __create_ovpn_config(self):
        """
        """
        if os.path.exists(self.dst_file):
            return dict(
                failed=False,
                changed=False,
                message=f"ovpn file {self.dst_file} exists."
            )

        if os.path.exists(self.key_file) and os.path.exists(self.crt_file):
            """
            """
            from jinja2 import Template

            with open(self.key_file, "r") as k_file:
                k_data = k_file.read().rstrip('\n')

            cert = self.__extract_certs_as_strings(self.crt_file)[0].rstrip('\n')

            tpl = "/etc/openvpn/client.ovpn.template"

            with open(tpl) as file_:
                tm = Template(file_.read())

            d = tm.render(
                key=k_data,
                cert=cert
            )

            with open(self.dst_file, "w") as fp:
                fp.write(d)

            self.__create_checksum_file(self.dst_file, self.dst_checksum_file)

            force_mode = "0600"
            if isinstance(force_mode, str):
                mode = int(force_mode, base=8)

            os.chmod(self.dst_file, mode)

            return dict(
                failed=False,
                changed= True,
                message = f"ovpn file successful written as {self.dst_file}."
            )

        else:
            return dict(
                failed=True,
                changed= False,
                message = f"can not find key or certfile for user {self._username}."
            )

    def __remove_ovpn_config(self):
        """
        """
        if os.path.exists(self.dst_file):
            os.remove(self.dst_file)

        if os.path.exists(self.dst_checksum_file):
            os.remove(self.dst_checksum_file)

        if self._creates and os.path.exists(self._creates):
            os.remove(self._creates)

        return dict(
            failed=False,
            changed=True,
            message=f"ovpn file {self.dst_file} successful removed."
        )

    def __extract_certs_as_strings(self, cert_file):
        """
        """
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

    def __validate_checksums(self):
        """
        """
        dst_checksum = None
        dst_old_checksum = None

        if os.path.exists(self.dst_file):
            with open(self.dst_file, "r") as d:
                dst_data = d.read().rstrip('\n')
                dst_checksum = self.__checksum(dst_data)

        if os.path.exists(self.dst_checksum_file):
            with open(self.dst_checksum_file, "r") as f:
                dst_old_checksum = f.readlines()[0]
        else:
            if dst_checksum is not None:
                dst_old_checksum = self.__create_checksum_file(self.dst_file, self.dst_checksum_file)

        if dst_checksum is None or dst_old_checksum is None:
            valid = False
        else:
            valid = (dst_checksum == dst_old_checksum)

        return valid

    def __create_checksum_file(self, filename, checksumfile):
        """
        """
        if os.path.exists(filename):
            with open(filename, "r") as d:
                _data = d.read().rstrip('\n')
                _checksum = self.__checksum(_data)

            with open(checksumfile, "w") as f:
                f.write(_checksum)

        return _checksum

    def __checksum(self, plaintext):
        """
        """
        _bytes = plaintext.encode('utf-8')
        _hash = hashlib.sha256(_bytes)
        return _hash.hexdigest()


# ===========================================
# Module execution.
#


def main():
    """
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(
                default="present",
                choices=["present", "absent"]
            ),
            force=dict(
                required=False,
                default=False,
                type="bool"
            ),
            username=dict(
                required=True,
                type="str"
            ),
            destination_directory=dict(
                required=True,
                type="str"
            ),
            chdir=dict(
                required=False
            ),
            creates=dict(
                required=False
            ),
        ),
        supports_check_mode=False,
    )

    o = OpenVPNOvpn(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
