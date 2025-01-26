#!/bin/sh

# wait for RabbitMQ server to start
sleep 10

cd etimsx
# run Celery worker for the project myproject with Celery configuration stored in Celeryconf
su -m myuser -c "celery worker -A myproject.celeryconf -Q default -n default@%h"