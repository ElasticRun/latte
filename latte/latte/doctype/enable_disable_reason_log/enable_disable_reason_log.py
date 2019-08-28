# -*- coding: utf-8 -*-
# Copyright (c) 2019, Sachin Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class EnableDisableReasonLog(Document):
	def after_insert(self):
		self.process_reason()

	def process_reason(self):
		if self.processed:
			return

		if not self.processed and self.ref_doctype and self.ref_name:
			frappe.db.set_value(self.ref_doctype, self.ref_name, 'disabled', self.disabled)
			frappe.get_doc({
			'doctype': 'Communication',
			'reference_name': self.ref_name,
			'reference_doctype': self.ref_doctype,
			'communication_type': 'Comment',
			'comment_type': 'Workflow',
			'content': f"""Doc updated reason: <b>{self.reason or 'NA'}</b>""",
			}).insert(ignore_permissions=True)

			frappe.db.set_value('Enable Disable Reason Log', self.name, 'processed', 1)