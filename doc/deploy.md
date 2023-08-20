# 部署

## Docker

### 准备工作

为减小镜像，用 pip 替代 [poetry][]，需将[`pyproject.toml`](https://python-poetry.org/docs/pyproject/)的`tool.poetry.dependencies`、`tool.poetry.group.deploy.dependencies`转换为[`requirements.txt`](https://pip.pypa.io/en/stable/reference/requirements-file-format/)。

```shell
$ poetry export --output requirements.txt --without-hashes --without-urls --with deploy
```

> **Note**
>
> [现在仓库中的`requirements.txt`](../requirements.txt)还手动删除了`python_version`、`sys_platform`，没考虑 python 3.9 和 3.10 依赖不同版本、Windows 和 Unix 不同等情况。之后出问题了再改。

### [Dockerfile](../Dockerfile)

1. 用 [pnpm][] 构建前端。
2. 设置用于生产的环境变量。
3. 安装依赖，整理静态文件，添加题库，启动服务。

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

然后参阅 [How to deploy Django | Django documentation | Django](https://docs.djangoproject.com/en/4.2/howto/deployment/)。

[just]: https://just.systems
[pnpm]: https://pnpm.io/
[poetry]: https://python-poetry.org
