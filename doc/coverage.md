# Coverage

利用 [coverage.py](https://coverage.readthedocs.io/) 评估测试的覆盖范围。（包括 python 代码和 Django 模板）

```shell
$ poetry install --with coverage
```

```shell
# 请在项目根目录运行

$ poetry run coverage run
$ poetry run coverage html
# 然后单击 htmlcov/index.html 链接
```

## 为何没加入`justfile`？

运行 Django 项目序号`manage.py`所在目录在`sys.path`上。`coverage run`会向`sys.path`加入`manage.py`所在目录，而`python -m coverage run`会加入当前目录。这种区别导致后者无法正常运行。

> **Note**
>
> 这与虚拟环境是否启用无关——`./.venv/Scripts/coverage.exe`和`./.venv/Scripts/python.exe -m coverage`同样符合上述描述。

如果要加入`justfile`，最好保证未启用虚拟环境也能正常工作。然而无虚拟环境时，`coverage`并不在`$PATH`上，只有`{{ python }} -m coverage`能可靠一致地被调用——`sys.path`和`$PATH`难以兼顾。

Mypy 提供了`mypy_path`配置 [import discovery](https://mypy.readthedocs.io/en/latest/command_line.html#import-discovery)，可解决`sys.path`的问题，从而`{{ python }} -m mypy`即可。很不幸 coverage.py 似乎没有类似机制。

考虑到无需一直关注测试覆盖范围，就不加入`justfile`了。
