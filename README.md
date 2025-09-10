# contest-bitnp 国防知识竞赛

[![Check](https://github.com/BITNP/contest-bitnp/actions/workflows/check.yml/badge.svg)](https://github.com/BITNP/contest-bitnp/actions/workflows/check.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/BITNP/contest-bitnp/main.svg)](https://results.pre-commit.ci/latest/github/BITNP/contest-bitnp/main)
[![Dockerhub image](https://img.shields.io/badge/dockerhub-image-important.svg?logo=Docker)](https://hub.docker.com/r/everything411/contest-bitnp)

> [!NOTE]
> GitHub 全年都会报告 Django 安全漏洞，而本项目只在夏秋之交使用。为减轻维护压力，每年会存档仓库；解除存档请联系[管理员](https://github.com/orgs/BITNP/people)。

## 目录

* [开发](#开发)
   * [开始](#开始)
      * [⚒️ 安装工具](#️-安装工具)
      * [👢 安装包](#-安装包)
      * [🏃‍♀️ 启动服务器](#️-启动服务器)
      * [✅ 检查](#-检查)
   * [VS Code](#vs-code)
      * [任务](#任务)
      * [Django 魔法](#django-魔法)
* [部署](#部署)
   * [容器部署](#容器部署)
      * [准备工作](#准备工作)
      * [构建容器镜像](#构建容器镜像)
      * [从头开始使用容器进行部署](#从头开始使用容器进行部署)
   * [手动部署](#手动部署)

## 开发

技术细节请参考[`doc/`](./doc/)。

> **Note**
>
> 还可参考 [GitHub Actions](./.github/workflows/check.yml)。

### 开始

#### ⚒️ 安装工具

##### [Poetry][poetry]

- **功能**：本项目使用 [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry] 管理 python 包。

  > 例如`poetry shell`可在终端直接使用虚拟环境。

- **安装方法**：请参阅 [Introduction | Documentation | Poetry](https://python-poetry.org/docs/#installation)。

- **配置**

  完成安装后，建议您选择[将虚拟环境放在项目中](https://python-poetry.org/docs/configuration/#virtualenvsin-project)：

  ```shell
  $ poetry config virtualenvs.in-project true
  ```

  > 原因：这样`poetry install`时会在项目所在文件夹创建`.venv/`，比`C:/Users/…/AppData/Local/pypoetry/Cache/…`或`~/.cache/pypoetry/…`更明显。

##### [Just][just]

- **功能**：本项目源代码不在根目录，有许多命令执行时有 tricks。因此建议安装 [just][]，用 just 调用。

  > 例如，运行 [mypy][] 时，必须使用正确配置在正确的位置运行。

  ```shell
  $ just --list  # 列出可用任务
  ```

- **安装方法（Unix）**

  建议参考 [Packages - Just Programmer's Manual](https://just.systems/man/en/chapter_4.html)，使用包管理器安装。

- **安装方法（Windows）**

  [下载编译好的可执行文件](https://github.com/casey/just/releases)，解压出`just.exe`，放到`$PATH`环境变量包含的任意地方。另外也可用包管理器 [scoop][] 安装：

  ```powershell
  > scoop install just
  ```

  在 Windows 上，除了 just，您还需要[选个 shell](https://just.systems/man/en/chapter_59.html)。至少有下面几种选择。

  - 将`C:/Program Files/Git/bin/`添加到`$PATH`环境变量，使用 Git for Windows 附带的 Git Bash（`sh.exe`）。

  - 也使用 Git Bash，但不用环境变量，而用 [scoop][] 包装：创建`~/scoop/shims/sh.shim`，写入`path = "C:/Program Files/Git/usr/sh.exe"`。

  - 编辑项目根目录的`justfile`，使用 Command Prompt 或 PowerShell。

    ```just
    # 在 justfile 开头加上以下任意一行
    set shell := ["cmd.exe", "/c"]
    set shell := ["powershell.exe", "-c"]
    # 更改后请勿提交到仓库中，因为CI和每人的设备不一样。
    ```

  > **Note**
  >
  > `C:/Program Files/Git/`指 Git 的安装目录。
  >
  > 另外注意是`…/Git/bin/`，而非`…/Git/usr/bin/`。

  > **Note**
  >
  > 可用[`--shell`](https://just.systems/man/en/chapter_59.html?highlight=--shell)临时测试，例如：
  >
  > ```shell
  > $ just --shell 'C:/Program Files/Git/usr/bin/bash.exe' …
  > ```

- **配置**

  如果需控制 just 使用哪个 python，请在项目根目录创建`.env`文件，设置`PYTHON`变量。下面是一些例子。

  ```toml
  # 使用项目中的虚拟环境
  PYTHON = "./.venv/Scripts/python.exe"

  # 使用 poetry 缓存中的环境
  PYTHON = "C:/Users/bjalp/AppData/Local/pypoetry/Cache/virtualenvs/…/python.exe"

  # 直接调用 poetry（万能，但比较慢）
  PYTHON = "poetry run python"
  ```

  > **Note**
  >
  > `poetry install`创建虚拟环境后，可用`poetry env info`查看“Executable”的位置。

##### [Pnpm][]

- **功能**：构建前端 CSS 和 JavaScript。

- **安装方法**

  1. 前往 [Node.js][nodejs] 网站，下载并安装 v18 LTS。（安装结束后会提示安装 choco，可取消勾选）

  2. 使用 corepack 安装 [pnpm][]。

     ```shell
     $ corepack enable
     $ corepack prepare pnpm@latest --activate
     ```

  > **Note**
  >
  > 也可尝试 [Installation | pnpm](https://pnpm.io/installation) 介绍的其它方法。

#### 👢 安装包

初次使用时，需要安装项目依赖的包并创建数据库：

```shell
$ just update
```

以后拉取他人提交后，如果他人更新了依赖或更改了数据模型，你可能无法继续开发，此时也请`just update`。

#### 🏃‍♀️ 启动服务器

1. 构建前端。

   ```shell
   $ just build-js build-theme
   ```

   > **Note**
   >
   > 如果你想更改前端代码，可`just watch-js`、`just watch-theme`来自动重新构建。

2. 启动 Django 服务器。

   ```shell
   $ just serve
   ```

3. 访问 [localhost:8000](http://localhost:8000)，用户名、密码请咨询他人。

#### ✅ 检查

- **代码质量**

  ```shell
  $ just check-all
  ```

  这会检查类型、运行测试等。

- **格式**（可选）

  本项目配置了 [pre-commit][]，可自动格式化代码、检查错别字等。

  如果你想使用它，那么可用 pip 或 [pipx][] 安装 pre-commit，然后运行`pre-commit install`。此后提交到仓库时会自动检查格式。

  > **Note**
  >
  > `git commit --no-verify`可绕过 pre-commit。

### VS Code

#### 任务

部分 just 命令配备了 problem matcher。<kbd>Ctrl</kbd>+<kbd>P</kbd>，输入`task`及空格，按提示操作可运行。

#### Django 魔法

VS Code 默认的 [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) 无法识别很多 Django 魔法（如`*_set`）。可考虑禁用之，代以 [Matan Gover 的 Mypy](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)。（也可并用）这需要你在工作区设置`mypy.dmypyExecutable`，目前的设置仅适用于 Windows。

## 部署

### 容器部署

#### 准备工作

为减小镜像，用 pip 替代 [poetry][]，需将[`pyproject.toml`](https://python-poetry.org/docs/pyproject/)的`tool.poetry.dependencies`、`tool.poetry.group.deploy.dependencies`转换为[`requirements.txt`](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

```shell
$ poetry export --output requirements.txt --without-hashes --without-urls --with deploy
```

> **Note**
>
> [现在仓库中的`requirements.txt`](./requirements.txt)还手动删除了`python_version`、`sys_platform`，没考虑 python 版本、操作系统不同的问题。之后出问题了再改。

#### 构建容器镜像

```shell
$ git clone https://github.com/BITNP/contest-bitnp
$ cd contest-bitnp
$ docker build -t everything411/contest-bitnp .
```

构建过程中会做以下几件事：

1. 用 [pnpm][] 构建前端。
2. 设置用于生产的环境变量。
3. 安装依赖，整理静态文件，添加题库，启动服务。

#### 从头开始使用容器进行部署

编写`docker-compose.yml`

```dockerfile
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

```shell
$ docker exec -it contest_web_1 bash
(in container) # python manage.py createsuperuser
(in container) # python manage.py loaddata fixtures/*.yml
```

### 手动部署

需要 [poetry][]、[just][]，安装方法及配置请参考上文。

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

> **Note**
>
> 若希望部署时永远开放答题，请`export DJANGO_DISABLE_QUIZ_OPENING_TIME_INTERVAL="任何非空字符串"`。

在 poetry 中安装部署依赖组后，可以使用 [uvicorn][] 或者 [gunicorn][] 来运行本网站：

使用 uvicorn 单线程运行：

```shell
$ export DJANGO_PRODUCTION=1
$ export SECRET_KEY="!!replace me replace me!!"
$ cd contest-bitnp
$ uvicorn contest.asgi::application
```

或者使用 gunicorn 管理多个 uvicorn 工作进程：

```shell
$ export DJANGO_PRODUCTION=1
$ export SECRET_KEY="!!replace me replace me!!"
$ cd contest-bitnp
$ gunicorn -w 4 -k uvicorn.workers.UvicornWorker contest.asgi:application
```

另请参阅 [How to deploy Django | Django documentation | Django](https://docs.djangoproject.com/en/4.2/howto/deployment/)。


[just]: https://just.systems
[mypy]: https://mypy.readthedocs.io
[nodejs]: https://nodejs.org
[pipx]: https://pypa.github.io/pipx/
[pnpm]: https://pnpm.io/
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/
[scoop]: https://scoop.sh
[uvicorn]: https://www.uvicorn.org/
[gunicorn]: https://gunicorn.org/
