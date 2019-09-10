import frappe

def lock(key, nowait=False):
    '''
        Distributed lock for a key
    '''
    lock_name = get_locked_key(key, nowait)
    if not lock_name:
        frappe.get_doc({
            'doctype': 'Lock',
            'key': key,
        }).db_insert()
        lock_name = get_locked_key(key, nowait)
    return lock_name

def get_locked_key(key, nowait):
    row = frappe.db.sql(f'''
        SELECT name
        from
            `tabLock`
        where
            `key` = %(key)s
        for update {"nowait" if nowait else ""}
    ''', {
        'key': key,
    })
    return row and row[0] and row[0][0]