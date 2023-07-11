# 开发指南

## 开始

本项目使用 [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/) 管理，您首先需要安装它，请参阅 [Introduction | Documentation | Poetry](https://python-poetry.org/docs/#installation)。

```shell
$ poetry install --with dev  # 安装依赖
$ poetry shell  # 使用虚拟环境
```

```shell
# 启动服务器
$ cd ./contest/
$ python ./manage.py runserver
```

## 设计

请参考[`doc/`](./doc/)。

## 类型检查

```shell
$ cd ./contest/
$ mypy . --config-file ../pyproject.toml
```
