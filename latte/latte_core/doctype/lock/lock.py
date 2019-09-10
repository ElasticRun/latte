# -*- coding: utf-8 -*-
# Copyright (c) 2019, Sachin Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from latte.utils.indexing import create_index

class Lock(Document):
	pass

def on_doctype_update():
	create_index('tabLock', ['key(280)'])

def remove_old_locks():
	return
	frappe.db.sql('delete from `tabLock` where modified < %(now)s - interval 15 minute', {
		'now': frappe.utils.now_datetime(),
	})
	frappe.db.commit()