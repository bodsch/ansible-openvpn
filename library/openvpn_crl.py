#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (c) 2022-2023, Bodo Schulz <bodo@boone-schulz.de>

from __future__ import absolute_import, division, print_function

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.crypto.plugins.module_utils.crypto.basic import (
    OpenSSLObjectError,
)
from ansible_collections.community.crypto.plugins.module_utils.crypto.module_backends.crl_info import (
    get_crl_info,
)
from ansible_collections.community.crypto.plugins.module_utils.crypto.support import (
    get_relative_time_option,
)


class OpenVPNCrl(object):
    """
    """
    module = None

    def __init__(self, module):
        """
        """
        self.module = module

        self.pki_dir = module.params.get('pki_dir')
        self.list_revoked_certificates = module.params.get('list_revoked_certificates')
        self.warn_for_expire = module.params.get('warn_for_expire')
        self.expire_in_days = module.params.get('expire_in_days')

        self.crl_file = f"{self.pki_dir}/crl.pem"

    def run(self):
        """
        """
        data = None

        try:
            with open(self.crl_file, 'rb') as f:
                data = f.read()
        except (IOError, OSError) as e:
            msg = f'Error while reading CRL file from disk: {e}'
            self.module.log(msg)
            self.module.fail_json(msg)

        if data:
            try:
                crl_info = get_crl_info(self.module, data, list_revoked_certificates=self.list_revoked_certificates)

                self.last_update = get_relative_time_option(crl_info.get('last_update'), 'last_update')
                self.next_update = get_relative_time_option(crl_info.get('next_update'), 'next_update')
                self.revoked_certificates = crl_info.get('revoked_certificates', [])

                result = dict(
                    failed = False,
                    last_update = dict(
                        raw = crl_info.get('last_update'),
                        parsed = self.last_update
                    ),
                    next_update = dict(
                        raw = crl_info.get('next_update'),
                        parsed = self.next_update
                    )
                )

                if self.warn_for_expire:
                    expired = self.expired(self.next_update)

                    result.update({
                        "expired": expired
                    })

                    if expired:
                        result.update({"warn": True})

                if self.list_revoked_certificates:
                    result.update({
                        "revoked_certificates": self.revoked_certificates
                    })

            except OpenSSLObjectError as e:
                msg = f'Error while decoding CRL file: {to_native(e)}'
                self.module.log(msg)
                self.module.fail_json(msg)

        return result

    def expired(self, next_update):
        """
        """
        from datetime import datetime

        result = False

        now = datetime.now()

        time_diff = next_update - now
        time_diff_in_days = time_diff.days

        self.module.log(f" - {time_diff_in_days} vs. {self.expire_in_days}")

        if time_diff_in_days <= self.expire_in_days:
            result = True

        self.module.log(f" - {result}")
        return result


def main():

    args = dict(
        state=dict(
            default="status",
            choices=["status"]
        ),
        pki_dir=dict(
            required=False,
            type="str",
            default="/etc/easy-rsa/pki"
        ),
        list_revoked_certificates = dict(
            required=False,
            type="bool",
            default=False
        ),
        warn_for_expire = dict(
            required=False,
            type="bool",
            default=True
        ),
        expire_in_days = dict(
            required=False,
            type="int",
            default=10
        )
    )

    module = AnsibleModule(
        argument_spec=args,
        supports_check_mode=False,
    )

    o = OpenVPNCrl(module)
    result = o.run()

    module.log(msg=f"= result: {result}")

    module.exit_json(**result)


# import module snippets
if __name__ == '__main__':
    main()


"""

# openssl crl  -text -noout -in  /etc/easy-rsa/pki/crl.pem
Certificate Revocation List (CRL):
        Version 2 (0x1)
        Signature Algorithm: sha512WithRSAEncryption
        Issuer: CN = Open VPN
        Last Update: Apr 24 03:51:14 2023 GMT
        Next Update: Apr 23 03:51:14 2024 GMT
        CRL extensions:
            X509v3 Authority Key Identifier:
                keyid:35:D2:22:90:B6:82:4A:DC:64:03:6B:17:8B:B0:07:E2:52:E0:60:1E
                DirName:/CN=Open VPN
                serial:64:41:E6:07:CC:D0:8E:1F:24:A8:F9:91:FC:34:0F:4B:47:06:D1:74
No Revoked Certificates.
    Signature Algorithm: sha512WithRSAEncryption
    Signature Value:
        d4:f4:fc:06:fa:ed:8b:cd:f4:eb:95:fb:88:c1:e8:ff:30:eb:
        e7:2a:ea:fa:8f:60:a6:07:81:a6:1a:aa:72:4b:68:7d:46:3a:
        7c:a2:3c:df:a3:7b:7b:85:0e:ba:1b:ba:06:13:04:74:0a:9c:
        27:60:ec:09:df:1a:3d:b6:3b:71:d1:20:4a:55:dc:47:e7:60:
        b5:65:82:09:ff:5d:e3:e2:4d:15:55:4f:1f:48:e8:c5:72:9b:
        a8:61:fd:17:8e:c4:4e:98:59:fa:58:6d:b1:a8:3a:b1:87:79:
        76:c2:9d:4a:3c:a3:54:e1:14:10:02:96:e9:fe:bf:6f:ab:2d:
        56:35:6e:94:9d:b1:aa:4f:d6:3c:b0:9a:29:8a:17:c6:7d:18:
        0c:15:fa:30:a9:c8:a5:22:63:79:cd:31:a0:1f:d0:38:be:93:
        c2:0f:be:73:97:2b:79:58:db:b9:bb:ec:aa:a9:f2:ac:cc:bb:
        4e:66:15:23:ae:1e:2b:86:40:79:4c:14:eb:58:e0:71:d7:3e:
        c8:93:11:e5:7a:e5:26:7a:94:c1:57:4b:75:ca:cb:92:c2:ca:
        87:a3:b8:16:7b:3d:53:13:23:70:04:c3:35:c7:41:29:06:9d:
        32:63:96:90:3d:4f:82:7a:23:08:9d:d7:85:d9:ad:9d:09:d2:
        e9:52:39:72:af:0d:4b:74:a2:39:c5:5c:80:4d:88:db:74:ae:
        87:a7:d3:cf:f3:0f:ae:44:94:bd:f8:21:c7:64:c7:bb:aa:46:
        68:ba:fb:42:37:ef:41:6f:0e:cb:c0:e9:c6:83:fb:15:8f:f0:
        a4:d4:2b:34:40:b0:89:b1:f7:d0:ce:c8:2c:3e:7d:7c:e4:37:
        c4:98:56:30:a2:42:89:36:fe:a8:3c:15:ec:fe:37:c7:a8:ba:
        78:39:70:54:c9:fc:6a:7f:05:5c:89:f3:4b:0f:c1:fe:1a:93:
        68:63:70:7b:ed:cb:82:85:3f:a2:8e:bc:d5:b7:21:b2:dc:2a:
        e9:79:a3:8f:a8:ad:9e:d4:f0:5a:13:18:2f:ea:bc:00:cf:e4:
        76:fb:fa:f4:cb:c3:b6:d4:d9:d4:b7:f1:eb:16:10:e9:69:93:
        64:fa:d3:f6:1b:9b:2f:7a:fb:6b:99:8d:7a:07:51:62:ed:fa:
        38:51:2a:e7:70:e9:a2:83:be:cf:a4:8d:5d:35:b6:49:7a:56:
        17:2a:a7:88:7d:6c:43:69:f3:67:f7:ce:69:97:5c:b8:ad:90:
        4e:9b:ab:cf:6c:52:a8:3e:54:09:61:8f:f3:7b:98:b3:a8:1f:
        75:6e:94:a1:c1:89:b8:f7:df:5c:7a:b7:13:47:c0:b1:42:03:
        c5:18:2a:77:6a:50:c9:8f

https://serverfault.com/questions/979826/how-to-verify-certificate-revocation-lists-against-multiple-certification-path
"""
