#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2023, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function
import re
# import os
# import sys

from ansible.module_utils.basic import AnsibleModule


class OpenVPN(object):
    """
    """
    module = None

    def __init__(self, module):
        """
        """
        self.module = module

        self._openvpn = module.get_bin_path('openvpn', True)

    def run(self):
        """
          runner
        """
        result = dict(
            failed=False,
            changed=False,
            version=None
        )

        args = []

        args.append(self._openvpn)
        args.append("--version")

        rc, out = self._exec(args)

        result['stdout'] = f"{out.rstrip()}"

        if rc == 0:
            pattern = re.compile(r"OpenVPN (?P<version>[0-9]+\.[0-9]+\.[0-9]+).*", re.MULTILINE)
            found = re.search(pattern, out.rstrip())

            if found:
                result['version'] = found.group('version')
        else:
            result['failed'] = True

        return result

    def _exec(self, commands):
        """
        """
        # self.module.log(msg="  commands: '{}'".format(commands))
        rc, out, err = self.module.run_command(commands, check_rc=False)
        if int(rc) != 0:
            self.module.log(msg=f"  rc : '{rc}'")
            self.module.log(msg=f"  out: '{out}'")
            self.module.log(msg=f"  err: '{err}'")
        return rc, out


# ===========================================
# Module execution.
#


def main():

    args = dict()

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
