from __future__ import unicode_literals, print_function

from six.moves import range
import requests
import frappe
import json
import os
import frappe.permissions

from frappe import _

from frappe.utils.csvutils import getlink
from frappe.utils.dateutils import parse_date
from frappe.utils.file_manager import save_url
import re
import csv
import os
from frappe.utils.csvutils import UnicodeWriter
from frappe.utils import cint, cstr, flt, getdate, get_datetime, get_url, get_absolute_url
from six import text_type, string_types
from frappe.utils.file_manager import get_file_path
import pandas as pd
import json
import frappe
import json
import os


def get_records_for_upload(import_doc):
	filename = get_file_path(import_doc.import_file)

	data = pd.read_excel(filename, skiprows=0)
	# print('upload_child')

	child_field_name=data.iloc[1:2].to_dict()
	child_field_name = child_field_name['Unnamed: 1'][1]
	# rename columns
	data.columns = list(data.iloc[7])
	child_data = data.iloc[11:]
	child_data = child_data.drop(['Column Name:'], axis=1)
	final_data = {}
	for parentid, j in child_data.groupby('parent'):
		for index, row in j.iterrows():
			child_rows = {}
			for act_row in row.keys():
				child_rows.update({act_row: row[act_row]})

			final_data.setdefault(parentid, []).append(child_rows)
	#         print('ch',child_rows,'\n\n')
	#     for m in j.iterrows():
	#         print('m--------',dict(m))
	# print(final_data)
	return final_data, child_field_name


@frappe.whitelist()
def upload_child(rows=None, submit_after_import=None, ignore_encoding_errors=False, no_email=True, overwrite=None,
				 update_only=None, ignore_links=False, pre_process=None, via_console=False, from_data_import="No",
				 skip_errors=True, data_import_doc=None, validate_template=False, user=None):
	"""upload data"""
	import_doc = frappe.get_doc('Data Import For Child', data_import_doc)
	data, child_field_name = get_records_for_upload(import_doc)

	def publish_progress(achieved, reload=False):
		total = 100
		if import_doc:
			frappe.publish_realtime("data_import_progress", {"progress": str(int(100.0 * achieved / total)),
															 "data_import": import_doc.name, "reload": reload}, user=frappe.session.user)

	import_log = []
	rollback_flag = None
	def log(**kwargs):
		if via_console:
			print((kwargs.get("title") + kwargs.get("message")).encode('utf-8'))
		else:
			import_log.append(kwargs)

	import_status = None
	error_flag = rollback_flag = False
	for i in data:
		try:
			doc = frappe.get_doc(import_doc.reference_doctype, i)
			print(i)
			for child_records in data[i]:
				print(child_records)
				doc.append(child_field_name, child_records)
			doc.save()
		except Exception as e:
			error_flag = True
			# build error message
			if frappe.local.message_log:
				err_msg = "\n".join(['<p class="border-bottom small">{}</p>'.format(
					json.loads(msg).get('message')) for msg in frappe.local.message_log])
			else:
				err_msg = '<p class="border-bottom small">{}</p>'.format(
					cstr(e))

			error_trace = frappe.get_traceback()
			if error_trace:
				error_log_doc = frappe.log_error(error_trace)
				error_link = get_absolute_url("Error Log", error_log_doc.name)
			else:
				error_link = None

			log(**{
				"row": i,
				"title": 'Error for row %s' % (i and frappe.safe_decode(child_records) or ""),
				"message": err_msg,
				"indicator": "red",
				"link": error_link
			})

			rollback_flag = True

		finally:
			frappe.local.message_log = []

	if error_flag and not rollback_flag:
		import_status = "Partially Successful"
	elif error_flag and rollback_flag:
		import_status = "Failed"
	else:
		import_status = "Successful"

	if rollback_flag:
		frappe.db.rollback()
	else:
		frappe.db.commit()

	log_message = {"messages": import_log, "error": error_flag}
	if import_doc:
		import_doc.log_details = json.dumps(log_message)

	import_doc.import_status = import_status
	import_doc.save()
	if import_doc.import_status in ["Successful", "Partially Successful"]:
		import_doc.submit()
		publish_progress(100, True)
	else:
		publish_progress(0, True)

	# used to save import status in data import for child
	frappe.db.commit()

@frappe.whitelist()
def export_data(doctype=None, child_doc=None):
	if child_doc:
		print('\n\n\nchild_doc', child_doc)
	exporter = ChildDataExporter(doctype=doctype, child_doc=child_doc, file_type='Excel')
	exporter.build_response()


class ChildDataExporter:
	def __init__(self, doctype=None, child_doc=None, file_type='Excel'):
		self.doctype = doctype
		self.child_doc = child_doc
		self.file_type = 'Excel'

		self.prepare_args()

	def prepare_args(self):
		return
		# if self.select_columns:
		# 	self.select_columns = parse_json(self.select_columns)
		# if self.filters:
		# 	self.filters = parse_json(self.filters)

		# self.docs_to_export = {}
		# if self.doctype:
		# 	if isinstance(self.doctype, string_types):
		# 		self.doctype = [self.doctype]

		# 	if len(self.doctype) > 1:
		# 		self.docs_to_export = self.doctype[1]
		# 	self.doctype = self.doctype[0]

		# if not self.parent_doctype:
		# 	self.parent_doctype = self.doctype

		# self.column_start_end = {}

		# if self.all_doctypes:
		# 	self.child_doctypes = []
		# 	for df in frappe.get_meta(self.doctype).get_table_fields():
		# 		self.child_doctypes.append(dict(doctype=df.options, parentfield=df.fieldname))

	def add_field_headings(self):
		self.writer.writerow(self.tablerow)
		self.writer.writerow(self.labelrow)
		self.writer.writerow(self.fieldrow)
		self.writer.writerow(self.mandatoryrow)
		self.writer.writerow(self.typerow)

	def build_response(self):
		self.writer = UnicodeWriter()
		self.add_main_header()
		self.tablerow = [self.doctype]
		self.labelrow = [_("Column Labels:")]
		self.fieldrow = ['Column Name:']
		self.mandatoryrow = [_("Mandatory:")]
		self.typerow = [_('Type:')]
		self.inforow = [_('Info:')]
		self.columns = []


		self._append_parent_column()
		self.build_field_columns(self.child_doc)

		self.add_field_headings()
		self.writer.writerow(['Start entering data below this line'])

		if self.file_type == 'Excel':
			self.build_response_as_excel()
		else:
			# write out response as a type csv
			frappe.response['result'] = cstr(self.writer.getvalue())
			frappe.response['type'] = 'csv'
			frappe.response['doctype'] = self.doctype

	def add_main_header(self):
		parent_doc = frappe.get_meta(self.doctype).as_dict()
		parentfield = None
		for i in parent_doc['fields']:
			if i['fieldtype'] =='Table' and i['options'] == self.child_doc:
				parentfield = i['fieldname']

		self.writer.writerow([_('Data Import Template')])
		self.writer.writerow(['parenttype', self.doctype])
		self.writer.writerow(['parentfield', parentfield])
		self.writer.writerow(['Child Table', self.child_doc])
		self.writer.writerow([''])
		self.writer.writerow(['DocType', self.child_doc])

	def build_response_as_excel(self):
		filename = frappe.generate_hash("", 10)
		with open(filename, 'wb') as f:
			f.write(cstr(self.writer.getvalue()).encode('utf-8'))
		f = open(filename)
		reader = csv.reader(f)

		from frappe.utils.xlsxutils import make_xlsx
		xlsx_file = make_xlsx(reader, "Data Import Template")

		f.close()
		os.remove(filename)

		# write out response as a xlsx type
		frappe.response['filename'] = self.doctype + '.xlsx'
		frappe.response['filecontent'] = xlsx_file.getvalue()
		frappe.response['type'] = 'binary'
		
	def build_field_columns(self, dt, parentfield=None):
		meta = frappe.get_meta(dt)

		self.tablerow
		self.labelrow
		self.fieldrow
		self.mandatoryrow
		self.typerow
		# build list of valid docfields
		tablecolumns = []

		meta = frappe.get_meta(self.child_doc)
		# meta.get_field()
		tablecolumns = []
		for f in frappe.db.sql('desc `tab%s`' % self.child_doc):
			field = meta.get_field(f[0])
			if field:
				tablecolumns.append(field)

		for docfield in tablecolumns:
			self.append_field_column(docfield=docfield)

	def append_field_column(self, docfield):
		self.fieldrow.append(docfield.fieldname)
		self.labelrow.append(_(docfield.label))
		self.mandatoryrow.append(docfield.reqd and 'Yes' or 'No')
		self.typerow.append(docfield.fieldtype)

	def _append_parent_column(self, dt=None):
		self.append_field_column(frappe._dict({
			"fieldname": "parent",
			"label": "Parent",
			"fieldtype": "Data",
			"reqd": 1,
		}))