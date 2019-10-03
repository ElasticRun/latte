import frappe
import pymysql
import sqlalchemy.pool as pool
from six import text_type
from markdown2 import UnicodeWithAttrs
from pymysql.constants import FIELD_TYPE
from pymysql.converters import conversions
from frappe.database import Database

conversions.update({
	FIELD_TYPE.NEWDECIMAL: float,
	FIELD_TYPE.DATETIME: frappe.utils.get_datetime,
	UnicodeWithAttrs: conversions[text_type]
})

con_pool = None

class PooledDatabase(Database):
	def __init__(self, host=None, user=None, password=None, db_name=None, autocommit=False):
		self.host = host or frappe.conf.db_host or 'localhost'
		self.user = user or frappe.conf.db_name
		self.password = password or frappe.conf.db_password
		self.db_name = db_name or self.user
		self.autocommit = autocommit
		self._conn = None

	def connect(self):
		global con_pool
		if not con_pool:
			con_pool = pool.QueuePool(lambda *_:self.get_connection(), max_overflow=10, pool_size=50)

		self._conn = con_pool.connect()
		self._cursor = self._conn.cursor()

	def check_transaction_status(self, *_, **__):
		pass

	def get_connection(self):
		return pymysql.connect(
			self.host,
			self.user,
			self.password,
			charset='utf8mb4',
			use_unicode=True,
			conv=conversions,
			db=self.db_name,
			autocommit=self.autocommit,
		)