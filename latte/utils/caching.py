import frappe
import inspect
from latte.utils.locking import lock
import pickle

def cache_me_if_you_can(expiry=20):
    def decorator(fn):
        arg_names = inspect.getfullargspec(fn).args
        def decorated(*args, **kwargs):
            for idx, arg in enumerate(args):
                kwargs[arg_names[idx]] = arg
            param_slug = frappe.as_json(kwargs, indent=None).replace('\"', '')
            method_name = f'{fn.__module__}.{fn.__name__}'
            slug = f"{method_name}**{param_slug}"
            cache = frappe.cache()
            cached_value = cache.get_value(slug)
            if cached_value:
                print('@@@@@@@@@@@@@@@@@@From Cache')
                return pickle.loads(cached_value)
            print('@@@@@@@@@@@@@@Cache miss', f'{fn.__module__}.{fn.__name__}')
            lock(slug)
            response = fn(**kwargs)
            cached_value = pickle.dumps(response)
            cache.set_value(slug, cached_value, expires_in_sec=expiry)
            return response
        return decorated
    return decorator