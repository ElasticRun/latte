FROM dock.elasticrun.in/er-frappe11-base:release
USER root
# Generate locale C.UTF-8 for mariadb and general locale dataopenjpeg
ENV LANG C.UTF-8

ARG GIT_AUTH_USER=gitlab-runner
ARG GIT_AUTH_PASSWORD=2Xr_xJuUPd2vLj9z-Aym

ENV GIT_AUTH_USER=${GIT_AUTH_USER}
ENV GIT_AUTH_PASSWORD=${GIT_AUTH_PASSWORD}

ARG LATTE_BRANCH=master
ARG GIT_LATTE_URL=engg.elasticrun.in/with-run/with-run-deployment/latte.git

ENV LATTE_URL=https://${GIT_AUTH_USER}${GIT_AUTH_PASSWORD:+:}${GIT_AUTH_PASSWORD}${GIT_AUTH_USER:+@}${GIT_LATTE_URL}

RUN cd /home/frappe/docker-bench && ./env/bin/pip install pygelf watchgod pandas
# Get-app latte
USER frappe
ARG CUR_DATE=2019-08-12
RUN cd /home/frappe/docker-bench && bench get-app --branch ${LATTE_BRANCH} ${LATTE_URL} && rm -rf /home/frappe/docker-bench/apps/latte/.git*
