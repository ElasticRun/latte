# print('Loading gevent patches')
# from gevent import monkey
# monkey.patch_all()
from latte.commands.utils import patch_all
patch_all()
import frappe
from os import environ
frappe.init(site=environ['site'])
frappe.connect()
frappe.local.lang = frappe.db.get_default("lang")
print(f'Loaded site {frappe.local.site}')
