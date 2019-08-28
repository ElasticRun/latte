redis_cache: redis-server config/redis_cache.conf
redis_socketio: redis-server config/redis_socketio.conf
redis_queue: redis-server config/redis_queue.conf
web: bench serve --port 8000
socketio: /usr/bin/node apps/frappe/socketio.js

watch: bench watch
flusher: bench redis-flush-on-reload

schedule: bench schedule
worker_short: bench worker --queue short --quiet
worker_long: bench worker --queue long --quiet
worker_default: bench worker --queue default --quiet
worker_fact: bench worker --queue fact --quiet
#migrator: bench migrate
#worker_event_dispatcher: bench eventdispatcher --queue kafka_events
async_event_dispatcher: bench aio-eventdispatcher --queue long
#worker_json_worker: bench jsonworker --queue kafka_events
