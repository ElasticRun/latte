frappe.pages['wr-dashboard'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("WR Dashboard"),
		single_column: true
	});

	frappe.wrdashboard = new Dashboard(wrapper);
	$(wrapper).bind('show', function () {
		frappe.wrdashboard.show();
	});

};

class Dashboard {

	constructor(wrapper) {
		this.wrapper = $(wrapper);
		$(`
		<div class="dashboard">
			<div class="filterdata row"></div>
			<div class="hr1 row"></div>
			<div class="hr2 row"></div>
			<div class="hr3 row"></div>
		</div>
		`).appendTo(this.wrapper.find(".page-content").empty());
		this.filterdata = this.wrapper.find(".filterdata");
		this.hr1 = this.wrapper.find(".hr1");
		this.hr2 = this.wrapper.find(".hr2");
		this.hr3 = this.wrapper.find(".hr3");
		this.page = wrapper.page;
	}

	show() {
		this.route = frappe.get_route();
		const current_dashboard_name = this.route.slice(-1)[0];

		if (this.dashboard_name !== current_dashboard_name) {
			this.dashboard_name = current_dashboard_name;
			this.page.set_title(this.dashboard_name);
			// this.set_dropdown();
			// this.container.empty();
			this.refresh();
		}
	}

	refresh() {
		this.get_dashboard_doc().then((doc) => {
			this.dashboard_doc = doc;
			frappe.call({
				method: 'latte.latte.doctype.dashboard_configuration.run',
				type: "GET",
				args: {
					dashboard_name: this.dashboard_name,
					filters: {}
				},
				freeze: true
			}).then((r) => {
				console.log("Response ", r);
			});
		});
	}

	get_dashboard_doc() {
		return frappe.model.with_doc('Dashboard Configuration', this.dashboard_name);
	}
}
