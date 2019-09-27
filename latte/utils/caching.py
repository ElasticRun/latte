import frappe
import inspect
import pickle
import gevent
from frappe.utils.redis_wrapper import RedisWrapper

PENDING = pickle.dumps('__PENDING__')

cache = None

def cache_me_if_you_can(expiry=5, build_expiry=30):
    def decorator(fn):
        arg_names = inspect.getfullargspec(fn).args
        def decorated(*args, **kwargs):
            logger = frappe.logger()
            global cache
            for idx, arg in enumerate(args):
                kwargs[arg_names[idx]] = arg

            param_slug = frappe.as_json(kwargs, indent=None).replace('\"', '')
            method_name = f'{fn.__module__}.{fn.__name__}'
            site_name = frappe.local.site
            slug = f"{site_name}-{method_name}**{param_slug}"

            if not cache:
                if frappe.local.conf.redis_big_cache:
                    cache = RedisWrapper.from_url(frappe.local.conf.redis_big_cache)
                else:
                    cache = frappe.cache()

            # print('SLUG=', slug)
            cached_value = cache.get(slug)
            # print('Cached Value', cached_value)
            if cached_value:
                cached_value = pickle.loads(cached_value)
                if cached_value == '__PENDING__':
                    gevent.sleep(1)
                    return decorated(**kwargs)
                # print('@@@@@@@@@@@@@@@@@@From Cache', slug)
                logger.debug(f'Serving {method_name} from cache')
                return cached_value

            exclusive = cache.set(slug, PENDING, nx=True, ex=build_expiry)
            logger.debug(f'Cache miss for {method_name}')
            if not exclusive:
                gevent.sleep(1)
                return decorated(**kwargs)

            try:
                response = fn(**kwargs)
            except:
                cache.delete(slug)
                raise

            cached_value = pickle.dumps(response)
            cache.set(slug, cached_value, ex=expiry)
            # print('set_value@@@', cache.get(slug))
            return response

        return decorated
    return decorator