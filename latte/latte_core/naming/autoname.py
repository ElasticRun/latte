import re
import frappe
import pymysql
import datetime
import sqlalchemy.pool as pool
from pymysql.err import OperationalError, ProgrammingError, InterfaceError
from frappe.database import Database
from frappe.utils import now_datetime
from six import string_types, text_type
from markdown2 import UnicodeWithAttrs
from pymysql.times import TimeDelta
from pymysql.constants import ER, FIELD_TYPE
from pymysql.converters import conversions

allowed_seq_names = re.compile('[a-z0-9A-Z_]')
con_pool = None

def lockless_autoname(doc, _=None):
    if doc.get('naming_series'):
        set_meta(doc)
        naming_series = doc.naming_series.replace('.', '').replace('#', '')
        digits = doc.naming_series.split('.')[-1].count('#') or 5
        doc.name = naming_series + getseries(naming_series, digits, 0)
        while frappe.db.get_value(doc.doctype, doc.name, 'name'):
            new_name = naming_series + getseries(naming_series, digits, 0)
            if new_name == doc.name:
                frappe.throw('Infinite Loop detected, failing')
            doc.name = new_name

def set_meta(doc):
    meta = frappe.get_meta(doc.doctype)
    if not (meta.autoname or '').startswith('naming_series:'):
        meta.autoname = 'naming_series:'

def update_series_table(key, value):
    frappe.db.sql('''
        UPDATE
            `tabSeries`
        set
            current = %(value)s
        where
            name = %(key)s
            and current < %(value)s
    ''', locals())
    frappe.db.commit()

def getseries(naming_series, digits, failures):
    # print('Parsing', naming_series, digits, failures)
    if failures > 5:
        frappe.throw('Unable to process sequence after 5 failures')
    next_val = None
    seq_name = 'naming_series_seq_' + frappe.scrub(naming_series)
    try:
        if not allowed_seq_names.match(str(seq_name)):
            frappe.throw('Bad sequence name detected, ' + seq_name)
        try:
            next_val = sql('select next value for ' + seq_name)[0][0]
            # print('NEXT_VAL=', next_val)
        except IndexError:
            return getseries(naming_series, digits, failures + 1)
        frappe.utils.background_jobs.enqueue(
            update_series_table,
            key=naming_series,
            value=next_val,
            enqueue_after_commit=True,
            queue='fact',
        )
    except ProgrammingError as e:
        if e.args[0] == 1146: #sequence not present
            current_value = frappe.db.sql('''
                SELECT
                    current
                from
                    `tabSeries`
                where
                    name = %(naming_series)s
                for update
            ''', {
                'naming_series': naming_series
            })

            start_with = 1
            if current_value:
                start_with = (current_value[0][0]) + 1

            sql('create sequence ' + seq_name + ' start with ' + str(start_with) + ' increment by 1 cache 1')
            return getseries(naming_series, digits, failures + 1)
        else:
            raise
    except (AttributeError, OperationalError, InterfaceError):
        return getseries(naming_series, digits, failures + 1)

    # print('value=', ('%0' + str(digits) + 'd') % next_val)
    return  ('%0' + str(digits) + 'd') % next_val

def get_conn():
    db_instance = Database()
    conversions.update({
        FIELD_TYPE.NEWDECIMAL: float,
        FIELD_TYPE.DATETIME: frappe.utils.get_datetime,
        UnicodeWithAttrs: conversions[text_type]
    })
    return pymysql.connect(
        db_instance.host,
        db_instance.user,
        db_instance.password,
        charset='utf8mb4',
        use_unicode = True,
        conv = conversions,
        local_infile = db_instance.local_infile,
        db = db_instance.user,
    )

def sql(query):
    global con_pool
    if not con_pool:
        con_pool = pool.QueuePool(get_conn, max_overflow=10, pool_size=50)
        sql('set autocommit=1')

    conn = con_pool.connect()
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        conn.close()
