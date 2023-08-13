FROM node:18-slim AS build
RUN corepack enable && corepack prepare pnpm@latest --activate
RUN pnpm config set registry https://registry.npmmirror.com/
COPY contest /usr/src/app
WORKDIR /usr/src/app
RUN pnpm --dir /usr/src/app/theme/static_src/ install && \
    pnpm --dir /usr/src/app/js/static_src/ install

RUN pnpm --dir /usr/src/app/theme/static_src/ run build && \
    pnpm --dir /usr/src/app/js/static_src/ run build && \
    rm -rf /usr/src/app/js/static_src/node_modules /usr/src/app/theme/static_src/node_modules

FROM python:3-slim
ENV DJANGO_PRODUCTION=1
ENV SECRET_KEY=dummy_secret_key_replace_me_please

RUN rm /etc/apt/sources.list.d/debian.sources
COPY deploy/sources.list /etc/apt/sources.list
RUN apt-get update && \
    apt-get install -y nginx tini && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /usr/src/app /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/requirements.txt
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install -r requirements.txt --no-cache-dir && \
    touch /usr/src/app/README.md && \
    python3 manage.py collectstatic --noinput

COPY deploy/entrypoint.sh /entrypoint.sh
COPY deploy/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD [ "/bin/bash", "/entrypoint.sh" ]
