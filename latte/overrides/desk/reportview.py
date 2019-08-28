import frappe
import json
from frappe.desk.reportview import get
from six import string_types
import pandas as pd

@frappe.whitelist()
def patched_get(*args, **kwargs):
    print(args, kwargs)
    doctype = kwargs.get('doctype')
    filters = kwargs.get('filters')
    if isinstance(filters, string_types):
        filters = json.loads(filters)
    if filters:
        validate_index(doctype, filters)
    return get(*args, **kwargs)

def validate_index(table_doctype, filters):
    return
    print(table_doctype, filters)
    doctype_filter = {}
    for doctype, field, comparator, value in filters:
        if comparator != '=' and comparator == 'like':
            if str(value or '').startswith('%'):
                continue
        else:
            continue

        doctype_filter.setdefault(doctype, set()).add(field)
    doctype_indices = {
        doctype: get_index_meta(doctype) for doctype in doctype_filter
    }
    doctype_indices[table_doctype] = get_index_meta(table_doctype)
    for doctype, filter_set in doctype_filter.items():
        for index_row in doctype_indices[doctype]['allowed_indices']:
            if set(index_row) <= filter_set:
                return
    else:
        if doctype_indices[table_doctype]['primary_cardinality'] < 10000:
            return
        frappe.msgprint(frappe.as_json(doctype_indices))
        frappe.msgprint('Without index query')

def get_index_meta(doctype):
    import pandas as pd
    table = f'tab{doctype}'
    cache_key = f'__index_meta_{table}'
    if hasattr(frappe.local, cache_key):
        return getattr(frappe.local, cache_key)
    cache = frappe.cache()
    index_meta = cache.get_value(cache_key)
    if index_meta:
        return index_meta
    indexed_columns = pd.read_sql(f'''
        SELECT
            column_name,
            index_name,
            seq_in_index,
            cardinality
        from
            information_schema.statistics
        where
            table_schema = '{frappe.conf.db_name}'
            and table_name = '{table}'
    ''', con=frappe.db._conn)
    index_cardinalities = indexed_columns.pivot(
        index='index_name',
        columns='seq_in_index',
        values=['column_name', 'cardinality'],
    )

    primary_cardinality = index_cardinalities.loc['PRIMARY']['cardinality'][1]
    row_scans = primary_cardinality / index_cardinalities.cardinality
    max_index_length = indexed_columns.seq_in_index.max()
    allowed_indices = []
    for index in row_scans.index:
        index_row = ()
        index_cols = index_cardinalities.column_name.loc[index]
        append = False
        for i in range(1, max_index_length + 1):
            scanned_rows = row_scans.loc[index].loc[i]
            if scanned_rows < 10000:
                index_row += (index_cols.loc[i],)
                append = True
                break
            else:
                index_row += (index_cols.loc[i],)

        if append:
            allowed_indices.append(index_row)
    #         print(scanned_rows)
    allowed_indices = list(set(allowed_indices))

    index_meta = {
        'allowed_indices': allowed_indices,
        'primary_cardinality': primary_cardinality,
    }
    cache.set_value(cache_key, index_meta)
    setattr(frappe.local, cache_key, index_meta)
    return index_meta
