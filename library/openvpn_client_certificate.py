#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import os
import sys
import hashlib

from ansible.module_utils.basic import AnsibleModule


class OpenVPNClientCertificate(object):
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

        self._chdir = module.params.get('chdir', None)
        self._creates = module.params.get('creates', None)

        self._openvpn = module.get_bin_path('openvpn', True)
        self._easyrsa = module.get_bin_path('easyrsa', True)

        self.req_file = os.path.join("pki", "reqs", f"{self._username}.req")
        self.key_file = os.path.join("pki", "private", f"{self._username}.key")
        self.crt_file = os.path.join("pki", "issued", f"{self._username}.crt")
        self.req_checksum_file = os.path.join("pki", "reqs", f".{self._username}.req.sha256")
        self.key_checksum_file = os.path.join("pki", "private", f".{self._username}.key.sha256")
        self.crt_checksum_file = os.path.join("pki", "issued", f".{self._username}.crt.sha256")

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

        if self.force and self._creates:
            self.module.log(msg="force mode ...")
            if os.path.exists(self._creates):
                self.module.log(msg=f"remove {self._creates}")
                os.remove(self._creates)

        if self._creates:
            if os.path.exists(self._creates):
                message = "nothing to do."
                if self.state == "present":
                    message = "user req already created"

                return dict(
                    changed=False,
                    message=message
                )

        args = []

        if self.state == "present":
            return self.__create_vpn_user()
        if self.state == "absent":
            return self.__revoke_vpn_user()

        rc, out = self._exec(args)

        result['result'] = f"{out.rstrip()}"

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
        if not self.__vpn_user_req():
            """
            """
            args = []

            # rc = 0
            args.append(self._easyrsa)
            args.append("--batch")
            args.append("build-client-full")
            args.append(self._username)
            args.append("nopass")

            rc, out = self._exec(args)

            if rc != 0:
                """
                """
                return dict(
                    failed=True,
                    changed=False,
                    message=f"{out.rstrip()}"
                )
            else:
                self.__create_checksum_file(self.req_file, self.req_checksum_file)
                self.__create_checksum_file(self.key_file, self.key_checksum_file)
                self.__create_checksum_file(self.crt_file, self.crt_checksum_file)

                return dict(
                    failed=False,
                    changed=True,
                    message = "client certificate successfuly created"
                )
        else:
            valid = self.__validate_checksums()

            if valid:
                return dict(
                    failed=False,
                    changed=False,
                    message="client certificate already created"
                )
            else:
                return dict(
                    failed=True,
                    changed=False,
                    message = "OMG, we have a problem!"
                )

    def __revoke_vpn_user(self):
        """
        """
        if not self.__vpn_user_req():
            return dict(
                failed=False,
                changed=False,
                message=f"no cert req for user {self._username} exists"
            )

        args = []

        # rc = 0
        args.append(self._easyrsa)
        args.append("--batch")
        args.append("revoke")
        args.append(self._username)

        rc, out = self._exec(args)

        if rc == 0:
            # recreate CRL
            args = []
            args.append(self._easyrsa)
            args.append("gen-crl")

        return dict(
            changed=True,
            failed=False,
            message=f"certificate for user {self._username} successfuly revoked"
        )

    def __vpn_user_req(self):
        """
        """
        if os.path.exists(self.req_file):
            return True

        return False

    def __validate_checksums(self):
        """
        """
        req_valid = False
        key_valid = False
        crt_valid = False

        req_checksum = None
        req_old_checksum = None

        key_checksum = None
        key_old_checksum = None

        crt_checksum = None
        crt_old_checksum = None

        if os.path.exists(self.req_file):
            with open(self.req_file, "r") as d:
                req_data = d.read().rstrip('\n')
                req_checksum = self.__checksum(req_data)

        if os.path.exists(self.req_checksum_file):
            with open(self.req_checksum_file, "r") as f:
                req_old_checksum = f.readlines()[0]
        else:
            if req_checksum is not None:
                req_old_checksum = self.__create_checksum_file(self.req_file, self.req_checksum_file)

        if os.path.exists(self.key_file):
            with open(self.key_file, "r") as d:
                key_data = d.read().rstrip('\n')
                key_checksum = self.__checksum(key_data)

        if os.path.exists(self.key_checksum_file):
            with open(self.key_checksum_file, "r") as f:
                key_old_checksum = f.readlines()[0]
        else:
            if crt_checksum is not None:
                key_old_checksum = self.__create_checksum_file(self.key_file, self.key_checksum_file)

        if os.path.exists(self.crt_file):
            with open(self.crt_file, "r") as d:
                crt_data = d.read().rstrip('\n')
                crt_checksum = self.__checksum(crt_data)

        if os.path.exists(self.crt_checksum_file):
            with open(self.crt_checksum_file, "r") as f:
                crt_old_checksum = f.readlines()[0]
        else:
            if crt_checksum is not None:
                crt_old_checksum = self.__create_checksum_file(self.crt_file, self.crt_checksum_file)

        if req_checksum is None or req_old_checksum is None or key_checksum is None or key_old_checksum is None or crt_checksum is None or crt_old_checksum is None:
            valid = False
        else:
            req_valid = (req_checksum == req_old_checksum)
            key_valid = (key_checksum == key_old_checksum)
            crt_valid = (crt_checksum == crt_old_checksum)

            valid = req_valid and key_valid and crt_valid

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

    def _exec(self, commands):
        """
          execute shell program
        """
        self.module.log(msg=f"  commands: '{commands}'")
        rc, out, err = self.module.run_command(commands, check_rc=True)
        # self.module.log(msg="  rc : '{}'".format(rc))
        # self.module.log(msg="  out: '{}'".format(out))
        # self.module.log(msg="  err: '{}'".format(err))
        return rc, out


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
            chdir=dict(
                required=False
            ),
            creates=dict(
                required=False
            ),
        ),
        supports_check_mode=False,
    )

    o = OpenVPNClientCertificate(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
