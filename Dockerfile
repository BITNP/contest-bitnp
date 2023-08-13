FROM python:3-slim
ENV DJANGO_PRODUCTION=1

COPY contest /usr/src/app
WORKDIR /usr/src/app

RUN rm /etc/apt/sources.list.d/debian.sources
COPY deploy/sources.list /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y nginx tini

ENV SECRET_KEY=dummy_secret_key_change_me_please
COPY poetry.lock /usr/src/app/poetry.lock
COPY pyproject.toml /usr/src/app/pyproject.toml
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install poetry --no-cache-dir && \
    touch /usr/src/app/README.md && \
    poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-dev && \
    python3 manage.py collectstatic --noinput

RUN rm -rf /usr/src/app/js/static_src/node_modules /usr/src/app/theme/static_src/node_modules && \
    rm -rf /var/lib/apt/lists/*

COPY deploy/entrypoint.sh /entrypoint.sh
COPY deploy/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "/bin/bash", "/entrypoint.sh" ]
