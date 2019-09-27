# -*- coding: utf-8 -*-
# Copyright (c) 2019, Sachin Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import format_datetime
from frappe.utils.file_manager import get_file_path
import pandas as pd
import json
import frappe
import json
import os
from latte.importer.doctype.data_import_for_child.child_import_export import upload_child


class DataImportForChild(Document):

	def autoname(self):
		if not self.name:
			self.name = "CH Import on " + format_datetime(self.creation)

	def validate(self):
		pass
		# if not self.import_file:
		# 	self.db_set("total_rows", 0)
		# if self.import_status == "In Progress":
		# 	frappe.throw(_("Can't save the form as data import is in progress."))

		# # validate the template just after the upload
		# # if there is total_rows in the doc, it means that the template is already validated and error free
		# if self.import_file and not self.total_rows:
		# 	upload(data_import_doc=self, from_data_import="Yes", validate_template=True)


@frappe.whitelist()
def import_data_for_child(data_import):
	print("i am here \n\n\n")
	frappe.db.set_value("Data Import For Child", data_import,
						"import_status", "In Progress", update_modified=False)
	frappe.publish_realtime("data_import_progress", {"progress": "0",
													 "ch_data_import": data_import, "reload": True}, user=frappe.session.user)

	from frappe.core.page.background_jobs.background_jobs import get_info
	enqueued_jobs = [d.get("job_name") for d in get_info()]

	if data_import not in enqueued_jobs:
		enqueue(upload_child, queue='default', timeout=6000, event='data_import_for_child', job_name=data_import,
				data_import_doc=data_import, from_data_import="Yes", user=frappe.session.user)
