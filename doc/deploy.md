# 部署

## 容器部署

### 准备工作

为减小镜像，用 pip 替代 [poetry][]，需将[`pyproject.toml`](https://python-poetry.org/docs/pyproject/)的`tool.poetry.dependencies`、`tool.poetry.group.deploy.dependencies`转换为[`requirements.txt`](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

```shell
$ poetry export --output requirements.txt --without-hashes --without-urls --with deploy
```

> **Note**
>
> [现在仓库中的`requirements.txt`](../requirements.txt)还手动删除了`python_version`、`sys_platform`，没考虑 python 3.9 和 3.10 依赖不同版本、Windows 和 Unix 不同等情况。之后出问题了再改。

### 构建容器镜像

```shell
$ git clone https://github.com/Phoupraw/contest-bitnp
$ cd contest-bitnp
$ docker build -t everything411/contest-bitnp .
```

构建过程中会做以下几件事：

1. 用 [pnpm][] 构建前端。
2. 设置用于生产的环境变量。
3. 安装依赖，整理静态文件，添加题库，启动服务。

### 从头开始使用容器进行部署

编写docker-compose.yml

```
version: "3"
services:
  web:
    image: everything411/contest-bitnp
    ports:
      - 8080:80
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DJANGO_PRODUCTION=1
    volumes:
     - ./db:/usr/src/app/db              # 数据库持久化
     - ./fixtures:/usr/src/app/fixtures  # 放fixtures，加载题目用
     # - ./settings.py:/usr/src/app/contest/settings.py # 取消注释可临时调整设置
```

然后

```shell
$ mkdir db
$ docker compose up -d
```

然后进去容器内部，创建超级管理员账号，导入：

```
$ docker exec -it contest_web_1 bash
(in container) # python manage.py createsuperuser
(in container) # python manage.py loaddata fixtures/*.yml
```

## 手动部署

需要 [poetry][]、[just][]，安装方法及配置请参考[`../DEVELOPMENT.md`](../DEVELOPMENT.md)。

> **Note**
>
> 可用`python -m venv`替代 poetry，手动执行替代 just。

```bash
$ export DJANGO_PRODUCTION="任何非空字符串"
$ export SECRET_KEY="The secret key must be a large random value and it must be kept secret"

$ echo 'PYTHON = "./.venv/bin/python"' > .env
$ just update  # 安装依赖、数据库等
$ just check-deploy  # 检查
```

在poetry中安装部署依赖组后，可以使用uvicorn或者gunicorn来运行本网站：

使用uvicorn单线程运行：

```shell
$ export DJANGO_PRODUCTION=1
$ export SECRET_KEY="!!replace me replace me!!"
$ cd contest-bitnp
$ uvicorn contest.asgi::application
```

或者使用gunicorn管理多个uvicorn工作进程：

```shell
$ export DJANGO_PRODUCTION=1
$ export SECRET_KEY="!!replace me replace me!!"
$ cd contest-bitnp
$ gunicorn -w 4 -k uvicorn.workers.UvicornWorker contest.asgi:application
```

另参阅 [How to deploy Django | Django documentation | Django](https://docs.djangoproject.com/en/4.2/howto/deployment/)。

[just]: https://just.systems
[pnpm]: https://pnpm.io/
[poetry]: https://python-poetry.org
