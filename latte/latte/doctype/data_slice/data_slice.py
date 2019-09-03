# -*- coding: utf-8 -*-
# Copyright (c) 2019, Sachin Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.desk.query_report import generate_report_result, get_report_doc


class DataSlice(Document):

    def execute(self):
        if self.data_source == 'Method':
            return frappe.call(self.method)
        if self.data_source == 'Report':
            report = get_report_doc(self.report)
            return generate_report_result(report=report)
        return "No Match Found"
