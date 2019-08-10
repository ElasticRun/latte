# -*- coding: utf-8 -*-
# Copyright (c) 2019, ElasticRun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from latte.utils import export_to_files
from six import string_types
import json

class View(Document):
	def validate(self):
		if self.is_standard and not self.module:
			frappe.throw('Module is mandatory to update a view if its standard')

	def on_update(self):
		export_to_files(self)
		self.create_view()

	def create_view(self):
		ctx = {
			row.key: (row.value or '') for row in self.ctx
		}
		query = self.view_query.format(**ctx)
		# print(query)

		# Trick to validate query before commit without running actual query
		frappe.db.sql(f'explain {query}', ctx)

		view_query = f'''
			CREATE or replace view `{self.name}`
			as (
				{query}
			)
		'''
		frappe.db.commit()
		frappe.db.sql(view_query, ctx)

	def set_ctx_value(self, key, value):
		try:
			key_row = [row for row in self.ctx if row.key == key][0]
			key_row.value = value
		except IndexError:
			self.append('ctx', {
				'key': key,
				'value': value,
			})