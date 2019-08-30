from __future__ import print_function
import frappe
from pymysql import InternalError, IntegrityError
from six import string_types
from frappe.model.dynamic_links import get_dynamic_links
from frappe.model.rename_doc import get_link_fields

def create_index(table, columns, unique=False):
    column_dict = {}
    if isinstance(columns, string_types):
        columns = [columns]
    for i, column_name in enumerate(columns[:]):
        length = None
        try:
            column_name, length = column_name.split('(')
            column_dict[column_name] = length[:-1]
            columns[i] = column_name
        except ValueError:
            pass
    already_indexed = frappe.db.sql('''
        SELECT
            group_concat(column_name order by seq_in_index) seq_idx
        from
            information_schema.statistics
        where
            table_name = %(table_name)s
            and non_unique = %(non_unique)s
        group by
            index_name
        having seq_idx = %(seq_idx)s
    ''', {
        'non_unique': int(not unique),
        'table_name': table,
        'seq_idx': ','.join(columns)
    })
    if already_indexed:
        return
    column_names = f'''"{'","'.join(columns)}"'''
    try:
        try:
            column_def = ', '.join([
                f"`{column_name}`{('(' + column_dict[column_name] + ')') if column_name in column_dict else ''}"
                for column_name in columns
            ])
            frappe.db.commit()
            frappe.db.sql(f'''
                CREATE
                    {'unique' if unique else ''}
                    index
                    {'unique_' if unique else ''}index_on_{'_'.join(columns)}
                on
                    `{table}`({column_def})
            ''')
            print(f'''Indexed {column_names} columns for table {table}, UNIQUE={unique}''')
            return True
        except InternalError as e:
            print(e)
            if int(e.args[0]) == 1061: #Handle duplicate index error
                pass
            elif int(e.args[0]) == 1170:
                print(f'''Error while creating index on table {table} column {column_names}''')
                print('=>', e)
                print('You should not create keys on columns which are text/blob.')
            else:
                raise
    except Exception as e:
        print(f'Error while creating index on table {table} column {column_names}')
        print('=>', e)

def index_all():
    frappe.db.commit()
    modified()
    contact_and_employee()
    field_name()
    lft_rgt_index()
    index_links()
    index_dynamic_links()
    index_default_tables()
    index_after_migrate()

def index_after_migrate():
    for hook in frappe.get_hooks('index_after_migrate'):
        indices = frappe.get_attr(hook)
        for index_meta in indices:
            create_index(*index_meta)

def index_default_tables():
    create_index('tabContact', 'mobile_no')
    create_index('tabDocShare', ['everyone', 'share_doctype'])
    create_index('tabDocShare', ['user', 'share_doctype', 'share_name'])
    create_index('tabEmail Queue', ['reference_doctype', 'reference_name'])
    create_index('tabFile', 'file_url(200)')
    create_index('tabFile', 'file_name')
    create_index('tabFile', 'content_hash')
    create_index('tabFile', 'is_attachments_folder')
    create_index('tabFile', 'is_home_folder')
    create_index('tabError Snapshot', 'timestamp')
    create_index('tabUser', ['user_type', 'enabled'])
    create_index('tabUser Permission', 'user')
    create_index('tabUser Permission', ['user', 'apply_to_all_doctypes', 'applicable_for'])
    create_index('tabUser Permission', ['user', 'applicable_for', 'allow'])
    create_index('tabVersion', ['ref_doctype', 'docname'])

def modified():
    tables_to_update = frappe.db.sql_list(f'''
        SELECT
            cols.table_name
        from
            information_schema.columns cols
        join
            information_schema.tables tabs
        on
            tabs.table_name = cols.table_name
            and tabs.table_schema = cols.table_schema
        where
            cols.column_name = "modified"
            and tabs.table_type = "BASE TABLE"
            and tabs.table_schema = "{frappe.conf.db_name}";
    ''')
    for table_name in tables_to_update:
        create_index(table_name, 'modified')

def contact_and_employee():
    create_index('tabContact', 'user')
    create_index('tabEmployee', 'user_id', True)

def field_name(destroy_first=False):
    doctypes_to_index = frappe.db.sql('''
        SELECT
            name,
            autoname
        from
            `tabDocType`
        where
            (issingle = 0 or issingle is null or issingle = "")
            and (istable = 0 or istable is null or istable = "")
            and autoname like "field:%%"
            and name not in (
                "Warehouse",
                "Sales Taxes and Charges Template",
                "Purchase Taxes and Charges Template",
                "Account",
                "Cost Center",
                "Department"
            )
    ''')
    for dt, field in doctypes_to_index:
        field = field.split(':')[-1]
        if field:
            try:
                if destroy_first:
                    frappe.db.sql('''
                        ALTER table
                            `tab{dt}`
                        drop index index_on_{field}
                    '''.format(dt=dt, field=field))
                create_index('tab{dt}'.format(dt=dt), field)
            except Exception as e:
                print('Error while creating field index',dt, field, e)

def lft_rgt_index():
    for table in frappe.db.sql_list('''
        SELECT
            table_name
        from
            information_schema.tables
        where
            table_name in ("tabCustomer Group", "tabTerritory", "tabItem Group", "tabWarehouse")
    '''):
        create_index(table, 'lft')
        create_index(table, 'rgt')

def index_dynamic_links():
    links = get_dynamic_links()
    links.sort(key=lambda x:x.get('parent'))
    for link in links:
        if frappe.get_meta(link.get('parent')).issingle:
            continue
        create_index('tab' + link.get('parent'), [link.get('options'), link.get('fieldname')])

def index_links():
    links = ([
        link
            for dt in frappe.get_all('DocType')
            for link in get_link_fields(dt.name)
    ])
    links.sort(key=lambda x:x.get('parent'))
    for link in links:
        if link.get('issingle'):
            continue
        create_index('tab' + link.get('parent'), link.get('fieldname'))
