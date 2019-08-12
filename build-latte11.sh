#! /bin/bash
TAG=$1
# Uses default frappe and bench master branches from github to build the docker image. Use own URLs to override.
#Temporarily uses docker branch from development project - not from deployment project.
echo "Kafka Config : '${KAFKA_CONFIG}'"
docker build -f Dockerfile --build-arg CUR_DATE=$(date +%Y-%m-%d:%H:%M:%S) --build-arg KAFKA_CONFIG='${KAFKA_CONFIG}' \
  --build-arg LATTE_BRANCH=docker --build-arg GIT_LATTE_URL=engg.elasticrun.in/with-run/latte.git \
  -t dock.elasticrun.in/er-latte11-base:${TAG} .
