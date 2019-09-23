# -*- coding: utf-8 -*-
# Copyright (c) 2019, Sachin Mane and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import cstr
from frappe.model.document import Document
from frappe.desk.query_report import generate_report_result, get_report_doc
from frappe.desk.reportview import compress, execute


class DashboardDataSlice(Document):

    def execute(self, filters=None):
        # TODO - Fix would be needed to not trigger multiple same reports for the one rendered on the Dashboard.
        # Also, Filters need to be streamlined. Processing happens on the front end.
        if self.data_source == 'Method':
            return frappe.call(self.method)
        if self.data_source == 'Report':
            report = get_report_doc(self.report)
            qry_filters = frappe._dict()
            if filters:
                filters = json.loads(filters)
                for fil in self.filter:
                    for gt_fl in filters.keys():
                        if gt_fl == fil.filter_data_slice:
                            qry_filters.update({
                                fil.mapped_filter_field: filters[gt_fl]
                            })
            if report.report_type == 'Report Builder':
                print(report.report_type)
                report_json = json.loads(report.json)
                report_fields = [rf[0] for rf in report_json.get('fields')]
                #frappe.local.form_dict.update(frappe._dict(
                vargs = frappe._dict(
                    doctype = report.ref_doctype,
                    fields = report_fields,
                    filters = qry_filters or []
                )
                return compress(execute(**vargs), args = vargs)
            return generate_report_result(report=report, filters=qry_filters or [])
        return None


# TODO - This function needs to be moved to a place other than this
# Fetches meta for Reports
@frappe.whitelist()
def generate_report_meta(report_name):
    report = get_report_doc(report_name)
    report_res = generate_report_result(report=report)
    return report_res.get('columns')
