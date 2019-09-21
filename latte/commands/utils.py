# -*- coding: utf-8 -*-

import click
import os
# import frappe
import importlib
import sys
from watchgod import run_process
from functools import wraps
from latte import _dict

def pass_context(f):
	@wraps(f)
	def _func(ctx, *args, **kwargs):
		return f(_dict(ctx.obj), *args, **kwargs)

	return click.pass_context(_func)

def get_site(context):
	try:
		site = context.sites[0]
		return site
	except (IndexError, TypeError):
		print('Please specify --site sitename')
		sys.exit(1)

def get_installed_apps():
	with open(os.path.abspath('./apps.txt')) as f:
		apps = [app for app in f.read().split('\n') if app]
	return apps

def patch_all():
	for app in get_installed_apps():
		try:
			importlib.import_module(f'{app}.monkey_patches')
		except ModuleNotFoundError:
			pass
		else:
			print(f'Loaded monkey patches from app {app}')

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

@click.command('gevent-worker')
@click.option('--queue', type=str)
@click.option('--noreload', 'no_reload',is_flag=True, default=False)
@click.option('--quiet', is_flag = True, default = False, help = 'Hide Log Outputs')
def gevent_worker(queue, quiet=False, no_reload=False):
	if not queue:
		raise Exception('Cannot run worker without queue')
	if no_reload:
		start_gevent_background_worker(queue, quiet)
	else:
		run_process(
			'../apps/',
			start_gevent_background_worker,
			args=(queue, quiet),
			min_sleep=4000,
			callback=show_changes,
		)
	# start_worker(queue, quiet=quiet)

def start_gevent_background_worker(queue, quiet):
	python_path = os.path.abspath('../env/bin/python')
	print('Starting gevent background worker for', queue)

	os.execv(python_path, [
		python_path,
		'-c',
		'\n'.join(line.strip() for line in f'''
			from gevent import monkey
			monkey.patch_all()
			from latte.commands.utils import patch_all
			patch_all()
			from latte.utils.background.gevent_worker import start
			start(queue="{queue}", quiet={quiet})
		'''.split('\n'))
	])

@click.command('serve')
@click.option('--port', default=8000)
@click.option('--noreload', "no_reload", is_flag=True, default=False)
def serve(port=None, profile=False, no_reload=False, sites_path='.', site=None):
	guni_path = os.path.abspath('../apps/latte/start_guni.py')
	python_path = os.path.abspath('../env/bin/python')
	print('Starting latte patched server at', guni_path)
	additional_flags = []
	if port:
		additional_flags += ['-b', f'0.0.0.0:{port}']

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
	site = get_site(context)
	ipython_path = os.path.abspath('../env/bin/ipython')
	os.execve(ipython_path, [
		ipython_path,
		'-i',
		'../apps/latte/ipython_loader.py'
	], _dict(os.environ).update({'site': site}))

@click.command('redis-flush-on-reload')
@pass_context
def watch_for_flush(context):
	"Flushes redis cache on reload"
	site = get_site(context)
	run_process(
		'../apps/',
		flushall,
		args=(site,),
		min_sleep=4000,
		callback=show_changes,
	)

@click.command('processlist')
@pass_context
def processlist(context):
	import frappe
	site = get_site(context)
	frappe.init(site=site)
	from frappe.commands.utils import find_executable
	mysql = find_executable('mysql')
	os.execv(mysql, [
		mysql,
		'-u',
		frappe.conf.db_name,
		f'-p{frappe.conf.db_password}',
		'--host',
		frappe.local.conf.db_host or '127.0.0.1',
		'-e',
		'show processlist'
	])

def flushall(site):
	import frappe
	frappe.init(site=site)
	print('Flushing redis cache')
	frappe.cache().flushall()

commands = [
	latte_worker,
	gevent_worker,
	serve,
	console,
	watch_for_flush,
	processlist,
]