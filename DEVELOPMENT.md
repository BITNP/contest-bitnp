# 开发指南

## 开始

本项目使用 [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/) 管理，您首先需要安装它，请参阅 [Introduction | Documentation | Poetry](https://python-poetry.org/docs/#installation)。

```shell
$ poetry install --with dev  # 安装依赖
$ poetry shell  # 使用虚拟环境
```

本项目源代码不在根目录，有许多命令执行时有 tricks。因此建议安装 [just](https://just.systems/man/en/chapter_1.html)，用 just 调用。

```shell
$ just --list  # 列出可用任务
```

## 合作

拉取他人提交后，如果他人更新了依赖或更改了数据模型，你可能无法继续开发。此时请`just update`。

## 设计

请参考[`doc/`](./doc/)。

## 类型检查

必须使用正确配置在正确的位置运行 mypy，因此建议用 just 调用。

```shell
$ just mypy
```

（`just check-all`就包括类型检查）

另外，VS Code 默认的 [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) 无法识别很多 Django 魔法（如`*_set`）。可考虑禁用之，代以 [Matan Gover 的 Mypy](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)。这需要你在工作区设置`mypy.dmypyExecutable`，目前的设置仅适用于 Windows。

## Django `manage.py`

可用`just manage`调用，例如……

```shell
$ just manage makemigrations
$ just manage migrate
```
