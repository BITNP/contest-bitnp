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

## 设计

请参考[`doc/`](./doc/)。

## 类型检查

必须使用正确配置在正确的位置运行 mypy，因此建议用 just 调用。

```shell
$ just mypy
```
