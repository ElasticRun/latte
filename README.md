## Latte

Frappe Latte

#### License

MIT

### Features

##### cache_me_if_you_can
You can use this method to cache output of any method for x seconds. All you'll have to do is decorate your function with `@cache_me_if_you_can`.   
This will also throttle multiple calls with similar parameters, executing only one call, and serving rest from cache, saving your server from redundant hits.
```
from latte.utils.caching import cache_me_if_you_can

@frappe.whitelist()
@frappe.read_only()
@cache_me_if_you_can(expiry=5)
def patched_get(*args, **kwargs):
    # print(args, kwargs)
    doctype = kwargs.get('doctype')
    filters = kwargs.get('filters')
```

##### Gevent BG worker
This is drop-in replacement of existing rq workers. Each gevent worker can process 500 (hardcoded) jobs concurrently (subject to max-connections in /etc/mysql/my.cnf). Use following procfile to start using gevent background workers. 
```
redis_cache: redis-server config/redis_cache.conf
redis_socketio: redis-server config/redis_socketio.conf
redis_queue: redis-server config/redis_queue.conf

web: bench serve --port 8000
socketio: /usr/bin/node apps/frappe/socketio.js

watch: bench watch
flusher: bench redis-flush-on-reload

schedule: bench schedule
worker_short: bench gevent-worker --queue short
worker_long: bench gevent-worker --queue long
worker_default: bench gevent-worker --queue default
spine_sub: bench aio-eventdispatcher --queue long
```
