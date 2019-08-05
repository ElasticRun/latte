redis_cache: redis-server config/redis_cache.conf
redis_socketio: redis-server config/redis_socketio.conf
redis_queue: redis-server config/redis_queue.conf
web: bench serve --port 8000
#--config $(pwd)/../apps/withrun_erpnext/guni_start.py \
#web: cd sites && ../env/bin/python ../apps/latte/start_guni.py -b 0.0.0.0:8000 -t 120 frappe.app:application --worker-connections 20 -k gevent --reload --access-logfile - --access-logformat  "{\"remote_ip\":\"%(h)s\",\"request_id\":\"%({X-Request-Id}i)s\",\"response_code\":%(s)s,\"request_method\":\"%(m)s\",\"request_path\":\"%(U)s\",\"request_querystring\":\"%(q)s\",\"request_timetaken\":%(D)s,\"response_length\":%(B)s}"

#webasync: ./env/bin/watchgod frasync.server.start.main apps/frasync/

socketio: /usr/bin/node apps/frappe/socketio.js

watch: bench watch
flusher: bench redis-flush-on-reload

schedule: bench schedule
worker_short: bench worker --queue short --quiet
worker_long: bench worker --queue long --quiet
worker_default: bench worker --queue default --quiet
worker_fact: bench worker --queue fact --quiet
#worker_event_dispatcher: bench eventdispatcher --queue kafka_events
#worker_json_worker: bench jsonworker --queue kafka_events
