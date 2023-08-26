#!/bin/bash
set -e
/usr/sbin/nginx
python3 manage.py migrate
gunicorn -w 4 --forwarded-allow-ips='*' -b unix:/tmp/gunicorn.sock -k uvicorn.workers.UvicornWorker contest.asgi:application
