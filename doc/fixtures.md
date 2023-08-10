# Fixtures

[`../fixtures/`](../fixtures/)是测试数据。

```shell
$ just manage loaddata ./fixtures/…
# 注意，只识别正斜杠。
```

## 来源

### `NGE.yaml`

从 [FGC:Main - EvaWiki](https://wiki.evageeks.org/FGC:Main) 复制得到`NGE.md`。

> **Note**
>
> 利用以下[用户样式](https://add0n.com/stylus.html)可隐藏不相关内容，方便复制。
>
> ```css
> @-moz-document url-prefix("https://wiki.evageeks.org/FGC:Episode_") {
> .fgc_scenelist td:nth-child(-n+2),
> .fgc_scenelist td:nth-child(n+4) {
>     display: none;
> }
> }
> ```

再用[`convert_md_fixture`](../scripts/convert_md_fixture.py)转换为`NGE.yaml`。

```shell
$ poetry run python ./scripts/convert_md_fixture.py ./fixtures/NGE.md
```

目前不常用，故不收入`justfile`。
