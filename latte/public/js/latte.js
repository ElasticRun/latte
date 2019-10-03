frappe.provide('latte');

async function capture_reason(document_type) {
  // for new creation do not ask reason
  if(cur_frm.doc.__islocal){
    return
  }

  const { message } = await frappe.db.get_value(document_type, {
    name: cur_frm.doc.name,
  }, 'disabled');


  if (message.disabled === cur_frm.doc.disabled) {
    return;
  }

  return new Promise(((resolve, reject) => {
    const dialog = new frappe.ui.Dialog({
      title: __('Please enter a Reason'),
      fields: [
        {
          fieldname: 'reason',
          options: 'Enable Reason',
          fieldtype: 'Link',
          label: 'Reason',
          reqd: 1,
          get_query() {
            return {
              query: 'latte.utils.doc_status_tracker.get_enable_disable_reason',
              filters: { disabled: cur_frm.doc.disabled, doctype: cur_frm.doc.doctype },
            };
          },
        },
      ],
    });

    if (cur_frm.doc.disabled === 1) {
      dialog.set_df_property('reason', 'options', 'Disable Reason');
    } else {
      dialog.set_df_property('reason', 'options', 'Enable Reason');
    }

    dialog.set_primary_action(__('Add Reasons'), (values) => {
      dialog.hide();
      const { reason } = values;
      frappe.xcall('latte.utils.doc_status_tracker.apply_doc_status_tracker', {
        ref_doctype: cur_frm.doc.doctype,
        docname: cur_frm.doc.name,
        reason,
        disabled: cur_frm.doc.disabled,
      }).then((newDoc) => {
        cur_frm.refresh();
      });
      resolve(values);
    });


    dialog.show();
  }));
}

frappe.db.get_list('Doc Status Tracker', {
  fields: ['document_type', 'is_active'],
  limit: 1000,
}).then((doctypes) => {
  doctypes.forEach(({ document_type }) => {
    frappe.ui.form.on(document_type, {
      before_save() {
        return capture_reason(document_type);
      },
    });
  });
});
