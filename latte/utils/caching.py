import frappe
import inspect
import pickle
import gevent

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
                if cached_value == '__PENDING__':
                    gevent.sleep(1)
                    return decorated(**kwargs)
                print('@@@@@@@@@@@@@@@@@@From Cache')
                return pickle.loads(cached_value)

            exclusive = cache.set(slug, '__PENDING__', nx=True)
            print('@@@@@@@@@@@@@@Cache miss', f'{fn.__module__}.{fn.__name__}', exclusive)
            if not exclusive:
                gevent.sleep(1)
                return decorated(**kwargs)
            try:
                response = fn(**kwargs)
            except:
                raise
            finally:
                cache.delete(slug)
            cached_value = pickle.dumps(response)
            cache.set_value(slug, cached_value, expires_in_sec=expiry)
            return response

        return decorated
    return decorator