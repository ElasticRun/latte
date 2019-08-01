# -*- coding: utf-8 -*-

import click
import os
import frappe
from watchgod import run_process
from frappe.commands import get_site, pass_context
from frappe.exceptions import AppNotInstalledError

def get_installed_apps():
	with open(os.path.abspath('./apps.txt')) as f:
		apps = f.read().split('\n')
	return apps

def patch_all():
	for app in get_installed_apps():
		try:
			pass
			# frappe.get_attr(f'{app}.monkey_patches')
		except (AttributeError, AppNotInstalledError):
			pass

def start_background_worker(queue, quiet):
	patch_all()
	from frappe.utils.background_jobs import start_worker
	print('Starting latte patched worker at', queue)
	start_worker(queue, quiet)

def show_changes(changes):
	print(changes)

@click.command('worker')
@click.option('--queue', type=str)
@click.option('--noreload', 'no_reload',is_flag=True, default=False)
@click.option('--quiet', is_flag = True, default = False, help = 'Hide Log Outputs')
def latte_worker(queue, quiet=False, no_reload=False):
	if not queue:
		raise Exception('Cannot run worker without queue')
	if no_reload:
		start_background_worker(queue, quiet)
	else:
		run_process(
			'../apps/',
			start_background_worker,
			args=(queue, quiet),
			min_sleep=4000,
			callback=show_changes,
		)
	# start_worker(queue, quiet=quiet)

@click.command('serve')
@click.option('--port', default=8000)
@click.option('--noreload', "no_reload", is_flag=True, default=False)
def serve(port=None, profile=False, no_reload=False, sites_path='.', site=None):
	guni_path = os.path.abspath('../apps/latte/start_guni.py')
	python_path = os.path.abspath('../env/bin/python')
	print('Starting latte patched server at', guni_path)
	additional_flags = []
	if port:
		additional_flags += ['-b', f'{port}']

	if not no_reload:
		additional_flags += ['--reload']

	os.execv(python_path, [
		python_path,
		guni_path,
	] + additional_flags)

@click.command('console')
@pass_context
def console(context):
	"Start ipython console for a site"
	patch_all()
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()
	frappe.local.lang = frappe.db.get_default("lang")
	import IPython
	IPython.embed(display_banner = "")

commands = [
	latte_worker,
	serve,
	console
]