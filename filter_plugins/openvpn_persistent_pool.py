# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.utils.display import Display

display = Display()


class FilterModule(object):
    """
        Ansible file jinja2 tests
    """

    def filters(self):
        return {
            'persistent_pool': self.persistent_pool,
            'clients_type': self.clients_type,
        }

    def persistent_pool(self, data):
        """
          Get the type of a variable
        """
        result = []

        for i in data:
            name = i.get('name')
            if i.get('static_ip', None) is not None:
                d = dict(
                    name=name,
                    state=i.get('state', 'present'),
                    static_ip = i.get('static_ip')
                )
                result.append(d)

        display.v(f" = result : {result}")
        return result

    def clients_type(self, data, type="static"):
        """

        """
        result = []

        for d in data:
            roadrunner = d.get("roadrunner", False)

            if type == "static" and not roadrunner:
                result.append(d)

            if type == "roadrunner" and roadrunner:
                result.append(d)

        display.v(f" = result : {result}")
        return result
