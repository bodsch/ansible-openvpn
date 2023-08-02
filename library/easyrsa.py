#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import os

from ansible.module_utils.basic import AnsibleModule


class EasyRsa(object):
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
        self._pki_dir = module.params.get('pki_dir', None)
        self._req_cn_ca = module.params.get('req_cn_ca', None)
        self._req_cn_server = module.params.get('req_cn_server', None)
        self._keysize = module.params.get('keysize', None)
        self._chdir = module.params.get('chdir', None)
        self._creates = module.params.get('creates', None)

        self._easyrsa = module.get_bin_path('easyrsa', True)

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
                self.module.log(msg=f"remove {self._creates}")
                os.remove(self._creates)

        if self._creates:
            if os.path.exists(self._creates):

                message = "nothing to do."

                if self.state == "init-pki":
                    message = "PKI already created"
                if self.state == "build-ca":
                    message = "CA already created"
                if self.state == "gen-crl":
                    message = "CRL already created"
                if self.state == "gen-dh":
                    message = "DH already created"
                if self.state == "gen-req":
                    message = "keypair and request already created"
                if self.state == "sign-req":
                    message = "certificate alread signed"

                return dict(
                    changed=False,
                    message=message
                )

        args = []
        args.append(self._easyrsa)

        if self.state == "init-pki":
            args.append(self.state)
            # args.append(f"--pki-dir={self._pki_dir}")

        if self.state == "build-ca":
            """
                easyrsa --batch --req-cn='{{ openvpn_req_cn_ca }}' build-ca nopass
            """
            args.append("--batch")
            # args.append(f"--pki-dir={self._pki_dir}")
            args.append(f"--req-cn={self._req_cn_ca}")

            if self._keysize:
                args.append(f"--keysize={self._keysize}")
            args.append(self.state)
            args.append("nopass")

        if self.state == "gen-crl":
            """
                ./easyrsa gen-crl
            """
            # args.append(f"--pki-dir={self._pki_dir}")
            args.append(self.state)

        if self.state == "gen-dh":
            """
                ./easyrsa gen-dh
            """
            if self._keysize:
                args.append(f"--keysize={self._keysize}")
            # args.append(f"--pki-dir={self._pki_dir}")
            args.append(self.state)

        if self.state == "gen-req":
            """
                ./easyrsa --batch --req-cn='{{ openvpn_req_cn_server }}' gen-req '{{ openvpn_req_cn_server }}' nopass
            """
            args.append("--batch")
            # args.append(f"--pki-dir={self._pki_dir}")
            args.append(f"--req-cn={self._req_cn_ca}")
            args.append(self.state)
            args.append(self._req_cn_server)
            args.append("nopass")

        if self.state == "sign-req":
            """
                ./easyrsa --batch sign-req server '{{ openvpn_req_cn_server }}'
            """
            args.append("--batch")
            # args.append(f"--pki-dir={self._pki_dir}")
            args.append(self.state)
            args.append("server")
            args.append(self._req_cn_server)

        rc, out = self._exec(args)

        result['result'] = f"{out.rstrip()}"

        if rc == 0:
            result['changed'] = True
        else:
            result['failed'] = True

        return result

    def _exec(self, commands):
        """
          execute shell program
        """
        # self.module.log(msg=f"  commands: '{commands}'")
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
            default="init-pki",
            choices=["init-pki", "build-ca", "gen-crl", "gen-dh", "gen-req", "sign-req"]
        ),
        pki_dir=dict(
            required=False,
            type="str"
        ),
        force=dict(
            required=False,
            default=False,
            type='bool'
        ),
        req_cn_ca=dict(
            required=False
        ),
        req_cn_server=dict(
            required=False
        ),
        keysize=dict(
            required=False,
            type="int"
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

    e = EasyRsa(module)
    result = e.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()
