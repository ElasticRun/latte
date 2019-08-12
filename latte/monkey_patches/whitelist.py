import frappe
import sys

old_whitelist = frappe.whitelist
def whitelist(allow_guest=False, xss_safe=False):
    return old_whitelist(allow_guest, xss_safe)
frappe.whitelist = whitelist