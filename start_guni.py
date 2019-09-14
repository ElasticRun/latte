# -*- coding: utf-8 -*-
import re
import sys

from gunicorn.app.wsgiapp import run
from gevent import monkey
monkey.patch_all()
# from latte.commands.utils import patch_all
# patch_all()
JSON_FORMAT = '''
    {
        "remote_ip":"%(h)s",
        "request_id":"%({X-Request-Id}i)s",
        "response_code":%(s)s,
        "request_method":"%(m)s",
        "request_path":"%(U)s",
        "request_querystring":"%(q)s",
        "request_timetaken":%(D)s,
        "response_length":%(B)s
    }
'''
SIMPLE_FORMAT = '%(m)s %(U)s %(q)s := %(s)s | %(D)s | %(B)s'
sys.argv += [
    '-t', '120',
    'latte.app:application',
    '--worker-connections', '40',
    '-w', '2',
    '-k', 'gevent',
    '--access-logfile', '-',
    '--access-logformat', SIMPLE_FORMAT,
]
if __name__ == '__main__':
    sys.exit(run())
