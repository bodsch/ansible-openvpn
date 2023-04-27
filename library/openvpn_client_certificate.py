#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import os
# import hashlib
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.bodsch.core.plugins.module_utils.directory import create_directory
from ansible_collections.bodsch.core.plugins.module_utils.checksum import Checksum

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

        self.checksum_directory = f"{Path.home()}/.ansible/cache/openvpn/{self._username}"

        self.req_checksum_file = os.path.join(self.checksum_directory, "req.sha256")
        self.key_checksum_file = os.path.join(self.checksum_directory, "key.sha256")
        self.crt_checksum_file = os.path.join(self.checksum_directory, "crt.sha256")

    def run(self):
        """
          runner
        """
        result = dict(
            failed=False,
            changed=False,
            ansible_module_results="none"
        )

        create_directory(self.checksum_directory)

        self.checksum = Checksum(self.module)

        if self._chdir:
            os.chdir(self._chdir)

        checksums_valid, msg = self.__validate_checksums()

        if checksums_valid:
            return dict(
                changed = False,
                message = msg
            )

        if self.force and self._creates:
            self.module.log(msg="force mode ...")
            if os.path.exists(self._creates):
                self.module.log(msg=f"remove {self._creates}")
                os.remove(self._creates)

        if self._creates:
            if os.path.exists(self._creates):
                message = "Nothing to do."
                if self.state == "present":
                    message = "The user request has already been created."

                return dict(
                    changed=False,
                    message=message
                )

        if self.state == "present":
            return self.__create_vpn_user()
        if self.state == "absent":
            return self.__revoke_vpn_user()

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
                req_checksum = self.checksum.checksum_from_file(self.req_file)
                self.checksum.write_checksum(self.req_checksum_file, req_checksum)

                key_checksum = self.checksum.checksum_from_file(self.key_file)
                self.checksum.write_checksum(self.key_checksum_file, key_checksum)

                crt_checksum = self.checksum.checksum_from_file(self.crt_file)
                self.checksum.write_checksum(self.crt_checksum_file, crt_checksum)

                return dict(
                    failed=False,
                    changed=True,
                    message = "The client certificate has been successfully created."
                )
        else:
            valid, msg = self.__validate_checksums()

            if valid:
                return dict(
                    failed=False,
                    changed=False,
                    message="The client certificate has already been created."
                )
            else:
                return dict(
                    failed=True,
                    changed=False,
                    message = msg
                )

    def __revoke_vpn_user(self):
        """
        """
        if not self.__vpn_user_req():
            return dict(
                failed=False,
                changed=False,
                message=f"There is no certificate request for the user {self._username}."
            )

        args = []

        # rc = 0
        args.append(self._easyrsa)
        args.append("--batch")
        args.append("revoke")
        args.append(self._username)

        rc, out = self._exec(args)

        if rc == 0:
            # remove checksums
            os.remove(self.checksum_directory)
            # recreate CRL
            args = []
            args.append(self._easyrsa)
            args.append("gen-crl")

        return dict(
            changed=True,
            failed=False,
            message=f"The certificate for the user {self._username} has been revoked successfully."
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
        msg = ""
        req_valid = False
        key_valid = False
        crt_valid = False

        req_checksum = None
        req_old_checksum = None

        key_checksum = None
        key_old_checksum = None

        crt_checksum = None
        crt_old_checksum = None

        req_changed, req_checksum, req_old_checksum = self.checksum.validate_from_file(self.req_checksum_file, self.req_file)
        key_changed, key_checksum, key_old_checksum = self.checksum.validate_from_file(self.key_checksum_file, self.key_file)
        crt_changed, crt_checksum, crt_old_checksum = self.checksum.validate_from_file(self.crt_checksum_file, self.crt_file)

        if os.path.exists(self.req_file) and not os.path.exists(self.req_checksum_file):
            req_checksum = self.checksum.checksum_from_file(self.req_file)
            self.checksum.write_checksum(self.req_checksum_file, req_checksum)
            req_changed = False

        if os.path.exists(self.key_file) and not os.path.exists(self.key_checksum_file):
            key_checksum = self.checksum.checksum_from_file(self.key_file)
            self.checksum.write_checksum(self.key_checksum_file, key_checksum)
            key_changed = False

        if os.path.exists(self.crt_file) and not os.path.exists(self.crt_checksum_file):
            crt_checksum = self.checksum.checksum_from_file(self.crt_file)
            self.checksum.write_checksum(self.crt_checksum_file, crt_checksum)
            crt_changed = False

        self.module.log("-------------------------------------------------------------------------")
        self.module.log(msg=f" - req {self.req_file} / {self.req_checksum_file}")
        self.module.log(msg=f"   changed     : {req_changed}")
        self.module.log(msg=f"   req checksum: {req_checksum}")
        self.module.log(msg=f"   old checksum: {req_old_checksum}")

        self.module.log(msg=f" - key {self.key_file} / {self.key_checksum_file}")
        self.module.log(msg=f"   changed     : {key_changed}")
        self.module.log(msg=f"   key checksum: {key_checksum}")
        self.module.log(msg=f"   old checksum: {key_old_checksum}")

        self.module.log(msg=f" - crt {self.crt_file} / {self.crt_checksum_file}")
        self.module.log(msg=f"   changed     : {crt_changed}")
        self.module.log(msg=f"   crt checksum: {crt_checksum}")
        self.module.log(msg=f"   old checksum: {crt_old_checksum}")


        # if (req_checksum is None or req_old_checksum is None) or (key_checksum is None or key_old_checksum is None) or (crt_checksum is None or crt_old_checksum is None):
        if req_changed or key_changed or crt_changed:
            _msg = []

            if req_changed:
                _msg.append(f"{self.req_checksum_file} are changed")
            if key_changed:
                _msg.append(f"{self.key_checksum_file} are changed")
            if crt_changed:
                _msg.append(f"{self.crt_checksum_file} are changed")

            msg = ", ".join(_msg)
            valid = False
        else:
            valid = True
            msg = "All Files are valid."

            # req_valid = (req_checksum == req_old_checksum)
            # key_valid = (key_checksum == key_old_checksum)
            # crt_valid = (crt_checksum == crt_old_checksum)
            #
            # valid = req_valid and key_valid and crt_valid

        self.module.log(msg=f"  valid     : {valid}")
        self.module.log("-------------------------------------------------------------------------")
        return valid, msg

        # if os.path.exists(self.req_file):
        #     with open(self.req_file, "r") as d:
        #         req_data = d.read().rstrip('\n')
        #         req_checksum = self.__checksum(req_data)
        #
        # if os.path.exists(self.req_checksum_file):
        #     with open(self.req_checksum_file, "r") as f:
        #         req_old_checksum = f.readlines()[0]
        # else:
        #     if req_checksum is not None:
        #         req_old_checksum = self.__create_checksum_file(self.req_file, self.req_checksum_file)
        #
        # if os.path.exists(self.key_file):
        #     with open(self.key_file, "r") as d:
        #         key_data = d.read().rstrip('\n')
        #         key_checksum = self.__checksum(key_data)
        #
        # if os.path.exists(self.key_checksum_file):
        #     with open(self.key_checksum_file, "r") as f:
        #         key_old_checksum = f.readlines()[0]
        # else:
        #     if crt_checksum is not None:
        #         key_old_checksum = self.__create_checksum_file(self.key_file, self.key_checksum_file)
        #
        # if os.path.exists(self.crt_file):
        #     with open(self.crt_file, "r") as d:
        #         crt_data = d.read().rstrip('\n')
        #         crt_checksum = self.__checksum(crt_data)
        #
        # if os.path.exists(self.crt_checksum_file):
        #     with open(self.crt_checksum_file, "r") as f:
        #         crt_old_checksum = f.readlines()[0]
        # else:
        #     if crt_checksum is not None:
        #         crt_old_checksum = self.__create_checksum_file(self.crt_file, self.crt_checksum_file)
        #
        # if req_checksum is None or req_old_checksum is None or key_checksum is None or key_old_checksum is None or crt_checksum is None or crt_old_checksum is None:
        #     valid = False
        # else:
        #     req_valid = (req_checksum == req_old_checksum)
        #     key_valid = (key_checksum == key_old_checksum)
        #     crt_valid = (crt_checksum == crt_old_checksum)
        #
        #     valid = req_valid and key_valid and crt_valid
        #
        # return valid

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
    args=dict(
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
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=False,
    )

    o = OpenVPNClientCertificate(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
