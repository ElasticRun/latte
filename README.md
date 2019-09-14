## Latte

Frappe Latte

#### License

MIT

### Features

##### cache_me_if_you_can
You can use this method to cache output of any method for x seconds. All you'll have to do is decorate your function. See https://engg.elasticrun.in/platform-foundation/latte/blob/0c68cc8a783428b2c1d1e764184ffba401a1b7dc/latte/overrides/desk/reportview.py#L11 for example.

##### Gevent BG worker
This is an drop-in replacement of existing workers. Each worker can process 500 jobs concurrently (subject to max-connections in /etc/mysql/my.cnf). Use following procfile to start using gevent background workers. 
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
