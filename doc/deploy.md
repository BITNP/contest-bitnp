# 部署

> **Warning**
>
> 尚未实际验证过，可能还需要修改`contest/contest/settings.py`。

需要 [poetry][]、[just][]，安装方法及配置请参考[`../DEVELOPMENT.md`](../DEVELOPMENT.md)。

> **Note**
>
> 如果实在困难，可用`python -m venv`替代 poetry，手动执行替代 just。

```bash
$ export DJANGO_PRODUCTION="任何非空字符串"
$ export SECRET_KEY="The secret key must be a large random value and it must be kept secret"

$ echo 'PYTHON = "./.venv/bin/python" > .env'
$ just update  # 安装依赖、数据库等
$ just check-deploy  # 检查

$ just serve  # 启动 Django 服务器（理论上只能用于开发）
```

## 另请参阅

[How to deploy Django | Django documentation | Django](https://docs.djangoproject.com/en/4.2/howto/deployment/)

[just]: https://just.systems
[poetry]: https://python-poetry.org
