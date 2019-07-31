# -*- coding: utf-8 -*-
import re
import sys

from gunicorn.app.wsgiapp import run
from gevent import monkey
monkey.patch_all()
import withrun_erpnext
sys.argv += [
    '-t', '120',
    'frappe.app:application',
    '--worker-connections', '20',
    '-k', 'gevent',
    '--access-logfile', '-',
    '--access-logformat', '''{
        "remote_ip":"%(h)s",
        "request_id":"%({X-Request-Id}i)s",
        "response_code":%(s)s,
        "request_method":"%(m)s",
        "request_path":"%(U)s",
        "request_querystring":"%(q)s",
        "request_timetaken":%(D)s,
        "response_length":%(B)s
    }'''
]
print(sys.argv)
if __name__ == '__main__':
    sys.exit(run())