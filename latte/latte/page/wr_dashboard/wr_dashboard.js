

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
		<style>
			.header {
				padding:5px;
				color: white;
				background-color: #0c7da9;
				text-transform: uppercase;
			}

			.slice_container {
				padding:10px;
				font-size: 40px;
				color: #fff;
				background-color: #065371;
			}
		</style>
		<div class="dashboard">
			<div class="filterdata row" style="margin-top:10px;"></div>
			<div class="hr1 row" style="margin-top:10px;"></div>
			<div class="hr2 row" style="margin-top:10px;"></div>
			<div class="hr3 row" style="margin-top:10px;"></div>
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
				this.renderUi(r);
			});
		});
	}

	renderUi(response) {
		if (response && response.message && response.message.data_slice_data) {
			const sliceData = response.message.data_slice_data;

			const hr1SliceData = [], hr2SliceData = [], hr3SliceData = [];
			for (let i = 0; i < sliceData.length; i++) {
				const dataSlice = sliceData[i];
				dataSlice.id_name = dataSlice.data_slice_name.replace(' ', '_');

				switch (dataSlice.dashboard_level) {
					case 'HR1': {
						hr1SliceData.push(dataSlice);
						break;
					} case 'HR2': {
						hr2SliceData.push(dataSlice);
						break;
					} case 'HR3': {
						hr3SliceData.push(dataSlice);
						break;
					}
				}
			}
			console.log("hr1SliceData", hr1SliceData);


			this.generateRowTemplate(hr1SliceData, this.hr1);
			this.generateRowTemplate(hr2SliceData, this.hr2);
			this.generateRowTemplate(hr3SliceData, this.hr3);

		}

	}

	generateRowTemplate(rows, container) {
		rows = this.sortByKey(rows, 'priority');
		for (let i = 0; i < rows.length; i++) {
			const sliceData = rows[i];
			switch (sliceData.data_type) {
				case 'Count': {
					const countObj = new DashboardCount(sliceData);
					container.append(countObj.getUiTemplate(this.getColCount(rows.length)));
					break;
				}
				case 'Table': {
					const tableObj = new DashboardTable(sliceData, container);
					break;
				}
			}
		}
	}

	get_dashboard_doc() {
		return frappe.model.with_doc('Dashboard Configuration', this.dashboard_name);
	}

	getColCount(size) {
		if (size < 6) {
			return Math.round(12 / size);
		}
	}


	sortByKey(array, key) {
		return array.sort((a, b) => {
			const x = a[key];
			const y = b[key];
			return ((x < y) ? -1 : ((x > y) ? 1 : 0));
		});
	}
}

class DashboardCount {
	constructor(data) {
		this.data = data;
	}

	getUiTemplate(col = 3) {
		let div = document.createElement("div");
		div.setAttribute("class", `col-xs-${col}`);
		div.innerHTML = `
				<div>
					<div class="header">
						<span>${this.data.data_slice_name}</span>
					</div>
				</div>
				<div>
					<div class="slice_container">
						<span id="open-orders-count">${this.data.result}</span>
					</div>
				</div>
			`;
		return div;
	}
}

class StationOpsGridView {
	constructor(params = {}) {
		this.debug = params.debug;
		this.slice_name = this.constructor.name;
		if (window.__loading_grid) {
			return;
		}
		window.__loading_grid = new Promise(async (resolve) => {
			await getLink('/assets/withrun_erpnext/css/grid_view.css');
			await getScript('/assets/withrun_erpnext/js/slickgrid/lib/jquery.event.drag-2.3.0.js');
			const loaders = [
				'slick.core.js',
				'slick.grid.js',
				'slick.dataview.js',
				'slick.grid.css',
				'css/smoothness/jquery-ui-1.11.3.custom.css',
				'css/bootstrap.css',
				'css/select2.css',
				'plugins/slick.autotooltips.js',
				'plugins/slick.cellcopymanager.js',
				'plugins/slick.cellexternalcopymanager.js',
				'plugins/slick.cellrangedecorator.js',
				'plugins/slick.cellrangeselector.js',
				'plugins/slick.cellselectionmodel.js',
				'plugins/slick.checkboxselectcolumn.js',
				'plugins/slick.draggablegrouping.js',
				'plugins/slick.headerbuttons.css',
				'plugins/slick.headerbuttons.js',
				'plugins/slick.headermenu.css',
				'plugins/slick.headermenu.js',
				'plugins/slick.rowdetailview.css',
				'plugins/slick.rowdetailview.js',
				'plugins/slick.rowmovemanager.js',
				'plugins/slick.rowselectionmodel.js',
			].map((file) => {
				if (file.endsWith('js')) {
					return getScript(`/assets/withrun_erpnext/js/slickgrid/${file}`);
				}
				return getLink(`/assets/withrun_erpnext/js/slickgrid/${file}`);
			});
			for (const loaderPromise of loaders) {
				await loaderPromise;// eslint-disable-line no-await-in-loop
			}
			resolve();
		});
		// console.log('slice_name=', this.constructor, this.slice_name);
	}

	log(...rest) {
		if (this.debug) {
			console.log(...rest);
			console.log(this.slice_name, this.debug);
		}
	}

	make_columns(columns, rowFormatters, additionalOptions = {}) {
		this.columns = columns.map((col) => {
			let formatter;
			let postFormatters;
			if (typeof col === 'object') {
				formatter = col.formatter; // eslint-disable-line prefer-destructuring
				postFormatters = col.postFormatters; // eslint-disable-line prefer-destructuring
				col = col.colString || col;
			}
			postFormatters = postFormatters || [];
			if (rowFormatters && rowFormatters.length) {
				postFormatters = postFormatters.concat(rowFormatters);
			}
			if (typeof col === 'string') {
				let [headerString, dfString, width] = col.split(':');
				let [label, fieldname] = headerString.split('/');
				fieldname = fieldname || frappe.scrub(label);
				width = width || 100;
				dfString = dfString || 'Data';
				let [fieldtype, option] = dfString.split('/');
				option = option || '';
				col = {
					label,
					fieldtype,
					width,
					fieldname,
					option,
				};
			}
			const label = col.label.split('_').map(i => i.charAt(0).toUpperCase() + i.substr(1)).join(' ');
			// this.log('col=', col);
			if (col.fieldtype === 'Check') {
				col.name = `<input type="checkbox" slice="${this.slice_name}" pos="-1" class="pull-left"></input>`;
			}
			return {
				label,
				fieldtype: col.fieldtype,
				width: parseInt(col.width, 10),
				// options: 'Brand',
				sortable: true,
				df: col,
				formatter: formatter || ((idx, colIdx, value, meta, item) => {
					value = (value === null || value === undefined) ? '' : value;
					this.log(value, item);
					let retVal;
					const fieldtype = meta.df ? meta.df.fieldtype : 'Data';
					switch (fieldtype) {
						case 'Link': retVal = `<a href="/desk#Form/${col.option}/${value}">${value}</a>`; break;
						case 'Currency': retVal = `₹ ${value}`; break;
						case 'Check':
							if (!value) {
								this.map(`input[type="checkbox"][slice="${this.slice_name}"][pos="-1"]`, (ip) => {
									// console.log(ip);
									ip.checked = false;
								});
							}
							retVal = `<input type="checkbox" ${value ? 'checked' : ''} slice="${this.slice_name}" pos="${idx}" class="pull-left"></input>`;
							break;
						case 'Array':
							retVal = `${value ? JSON.parse(value).join(',') : ''}`;
							break;
						case 'Boolean':
							retVal = !!value;
							break;
						case 'Data':
						default:
							retVal = value;
					}
					for (let i = 0; i < postFormatters.length; i++) {
						const fn = postFormatters[i];
						retVal = fn(idx, colIdx, value, meta, item, retVal);
					}
					return retVal;
				}),
				field: col.fieldname,
				id: col.fieldname,
				name: col.name || col.label,
			};
		});
		// this.checkboxSelector = new Slick.CheckboxSelectColumn({
		//   cssClass: 'slick-cel-checkboxsel',
		// });
		// this.columns.push(this.checkboxSelector.getColumnDefinition());
		this.slickgrid_options = {
			enableColumnReorder: false,
			enableCellNavigation: true,
			showHeaderRow: true,
			headerRowHeight: 30,
			explicitInitialization: true,
			multiColumnSort: true,
		};
		Object.assign(this.slickgrid_options, additionalOptions);

		this.inlineFilters = function inlineFilter(item) {
			const { columnFilters } = _args;// eslint-disable-line no-undef
			// const dataTypeComparators = {
			//   Date: (a, b) => a.getTime() < b.getTime(),
			//   Currency: (a, b) => parseFloat(a) < parseFloat(b),
			//   default: (a, b) => `${a}`.localeCompare(`${b}`),
			// };
			// console.log('columnFilters=', columnFilters, _args);// eslint-disable-line no-undef
			// const comparator = dataTypeComparators[]
			// const comparators = {
			// '>': (a, b) => ,
			// };
			for (const key in columnFilters) {
				if (Object.prototype.hasOwnProperty.call(columnFilters, key)) {
					const searchVal = columnFilters[key] || '';
					if (!(`${item[key]}`).toLowerCase().includes(searchVal.toLowerCase())) {
						return false;
					}
				}
			}
			return true;
		};
	}

	reRenderRows(rows, data) {
		if (data) {
			const items = data.map((so, i) => Object.assign({
				id: `_${i + 1}`,
				no: (i + 1),
			}, so));
			this.dataView.setItems(items);
		}
		this.grid.invalidateRows(rows);
		this.grid.render();
	}

	reRender(data) {
		const items = data.map((so, i) => Object.assign({
			id: `_${i + 1}`,
			no: (i + 1),
		}, so));
		this.dataView.setItems(items);
		this.grid.invalidate();
	}

	async make(selector, items) {
		await window.__loading_grid;
		this.make_columns();
		const me = this;
		this.columnFilters = {};
		items = items || [];
		items = items.map((so, i) => Object.assign({
			id: `_${i + 1}`,
			no: (i + 1),
		}, so));
		const dataView = this.dataView = new Slick.Data.DataView({ inlineFilters: true });
		if (this.getItemMetadata) {
			dataView.getItemMetadata = this.getItemMetadata(dataView.getItemMetadata);
		}
		dataView.beginUpdate();
		dataView.setFilter(this.inlineFilters);
		dataView.setFilterArgs({
			columns: this.columns,
			columnFilters: this.columnFilters,
		});
		dataView.setItems(items);
		dataView.endUpdate();
		this.dataView.onRowCountChanged.subscribe((e, args) => {
			// this.update_totals_row();
			this.grid.updateRowCount();
			this.grid.render();
		});

		this.dataView.onRowsChanged.subscribe((e, args) => {
			this.grid.invalidateRows(args.rows);
			this.grid.render();
		});
		this.grid = new Slick.Grid(selector, this.dataView, this.columns, this.slickgrid_options);
		this.grid.setSelectionModel(new Slick.CellSelectionModel());
		// this.grid.setSelectionModel(new Slick.RowSelectionModel({ selectActiveRow: false }));
		// this.grid.registerPlugin(this.checkboxSelector);
		// const columnpicker = new Slick.Controls.ColumnPicker(this.columns, this.grid, this.slickgrid_options);
		this.grid.registerPlugin(new Slick.CellExternalCopyManager({
			dataItemColumnValueExtractor(item, columnDef, value) {
				return item[columnDef.field];
			},
		}));
		$(this.grid.getHeaderRow()).delegate(':input', 'change keyup', function keyupHandler(e) {
			const columnId = $(this).data('columnId');
			if (columnId != null) {
				me.columnFilters[columnId] = $.trim($(this).val());
				me.dataView.refresh();
			}
		});

		this.grid.onHeaderRowCellRendered.subscribe((e, args) => {
			$(args.node).empty();
			// console.log(this.columnFilters);
			$("<input type='text'>")
				.data('columnId', args.column.id)
				.val(me.columnFilters[args.column.id])
				.appendTo(args.node);
		});
		this.grid.init();
		StationOpsGridView.prototype.bind_events.call(this);
	}

	map(selector, fn, iffn) {
		// console.log(this);
		return Array.prototype.map.call(
			Array.prototype.filter.call(this.wrapper.find(selector), iffn || (() => true)),
			fn,
		);
	}

	bind_events() {
		if (!this.grid) {
			return;
		}
		try {
			this.grid.onClick.subscribe((e, args) => {
				if (this.onClick) {
					this.onClick(e, args);
				}
			});
		} catch (e) {
			console.log(e);
		}

		this.wrapper.on('click', `input[type="checkbox"][slice="${this.slice_name}"][pos="-1"]`, (event) => {
			const dataView = this.grid.getData();
			const viewLength = dataView.getLength();
			const affectedItems = [];
			for (let i = 0; i < viewLength; i++) {
				const item = dataView.getItem(i);
				item.selected = event.currentTarget.checked;
				affectedItems.push(item);
			}
			const itemCheckSelector = `input[type="checkbox"][slice="${this.slice_name}"][pos!="-1"]`;
			this.map(itemCheckSelector, (ip) => {
				ip.checked = event.currentTarget.checked;
			});
			if (this.onSelectionChange) {
				this.onSelectionChange(affectedItems);
			}
			// const data = this.grid.getData().getItems().forEach((row) => {
			//   row.selected = event.currentTarget.checked;
			// });
		});
		this.wrapper.on('change', `input[type="checkbox"][slice="${this.slice_name}"][pos!="-1"]`, (event) => {
			const data = this.grid.getData();
			const item = data.getItem(event.currentTarget.getAttribute('pos'));
			item.selected = event.currentTarget.checked;
			if (this.onSelectionChange) {
				this.onSelectionChange([item]);
			}
			// window.__sad = event;
			// console.log(event);
		});
	}

	getSelectedNames() {
		const data = this.grid.getData().getItems();
		return data.filter(item => item.selected).map(item => item.name);
	}
};

class DashboardTable extends StationOpsGridView {
	constructor(data, container) {
		super();
		this.columns = data.result.columns;
		this.data = data;
		this.container = container;
		this.make_dom();
		let res = this.data.result.result;
		let createdData = []
		for (let i = 0; i < res.length; i++) {
			const element = res[i];
			const x = {};
			for (let j = 0; j < this.columns.length; j++) {
				const key = this.columns[j];
				x[key] = element[j]
			}
			createdData.push(x);
		}
		super.make(`.${this.data.id_name}`, createdData);
	}

	make_dom() {
		this.container.append(`
      <div class="" style="margin:10px;">
        <div><h2>${this.data.data_slice_name}</h2></div>
        <div class="${this.data.id_name}" style="height:400px">
        </div>
      </div>
    `);
	}

	make_columns() {
		super.make_columns(this.columns);
	}
}



function getScript(url) {
	return new Promise((resolve, reject) => {
		$.ajax({
			url,
			dataType: 'script',
			cache: true,
			success: resolve,
			error: reject,
		});
	});
}

function getLink(url) {
	return new Promise(((resolve, reject) => {
		const link = document.createElement('link');
		link.setAttribute('rel', 'stylesheet');
		link.setAttribute('type', 'text/css');
		link.onload = resolve;
		link.onerror = reject;
		link.setAttribute('href', url);
		document.getElementsByTagName('head')[0].appendChild(link);
	}));
}