# Fixtures

[`../fixtures/`](../fixtures/)是测试数据。

```shell
# YAML fixture → 数据库
$ just manage loaddata ./fixtures/….yaml
# 注意，只识别正斜杠。
```

```shell
# 清空题库
$ just shell
>>> from quiz.models import Question
>>> Question.objects.all().delete()
```

> [!TIP]
>
> 上面的命令只能清除格式正确时的题库数据。如果导入过错误的数据，上面的命令没有用，可以考虑直接删除整个数据库（删除`/contest/db.sqlite3`）。

## 命名规定

接近数据库称作 load，接近人称作 dump。

```mermaid
flowchart LR
    人类可读格式 -->|"scripts/load_*"| yaml[YAML fixture] -->|"manage loaddata"| 数据库
        -->|"manage dumpdata"| yaml -->|"scripts/dump_*"| 人类可读格式
    数据库 -->|"manage dump_*"| 人类可读格式
```

## 格式

### Simple Markdown

- 忽略空行。
- 起头依次为`#`、空格的行表示题干，其余为选项。
- `【应选】`开头的选项应选，其余不应选。
- 紧随题干的选项是该题的选项。
- 选项仅包含“正确”“错误”的题目为判断题，其余为单项选择题。

```shell
# 数据库 → 人类可读格式
$ just manage dump_md > ./fixtures/….md

# 人类可读格式 → YAML fixture
$ python ./scripts/load_md.py ./fixtures/….md
```

标准示例：

```markdown
# 中国人民解放军诞生于（ ）

【应选】1927年8月1日

1949年8月1日

1927年10月1日

1949年10月1日
```

能接受但不推荐的例子：

```markdown
#   Hedgehog's Dilemma - B

        Campfire Chat ~ Retrieval
    The Square Peg
Unexpected Farewell ~ Making Things Even
【应选】    "Welcome Home"
```

## 其它格式

下面这些格式只在迁移、测试时需要，一般可以忽略。

### `NGE.yaml`

> [!WARNING]
>
> [`NGE.md`](../fixtures/NGE.md)并非 simple markdown 格式。另外，NGE的数据并不规范，例如判断题可能有不知两个选项。

从 [FGC:Main - EvaWiki](https://wiki.evageeks.org/FGC:Main) 复制得到`NGE.md`。

> [!NOTE]
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

再用[`load_nge`](../scripts/load_nge.py)转换为`NGE.yaml`。

```shell
$ poetry run python ./scripts/load_nge.py ./fixtures/NGE.md --first-correct
```

目前不常用，故不收入`justfile`。

### `problems.yaml`

来自 PHP 旧项目。

```shell
$ poetry run python ./scripts/load_problems_csv.py ./fixtures/problems.csv
```
