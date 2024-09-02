# 导出

```shell
$ poetry install --with agg
```

## 流程

### 从服务器导出

在`just shell`中运行以下内容（运行`just shell`，然后粘贴进去），定稿所有超期答卷。

```python
from quiz.models import DraftResponse
from quiz.views import continue_or_finalize

for r in DraftResponse.objects.all():
    print(continue_or_finalize(r))
```

利用`just manage dumpdata`导出数据，然后下载到本地。（数据量大，而服务器资源有限）

```shell
$ just manage dumpdata quiz contenttypes auth --format jsonl --output db.jsonl
```

> [!NOTE]
>
> - 这里只导出了`quiz`相关数据，文件会小几 MB。
> - JSON lines（`*.jsonl`）格式每行一条记录，方便检查。

### 在本地统计

清空本地数据库再创建空表，然后导入下载下来的数据。

```shell
$ rm ./contest/db.sqlite3 && just manage migrate
$ just manage loaddata db.jsonl --verbosity 3
```

再在`just shell`中运行以下内容，导出分数为`scores.csv`。

```python
"""导出分数"""

from collections import deque
from pathlib import Path

from django.db.models import Prefetch
from quiz.models import Response, Student
from rich.progress import track

data = deque()

for s in track(
    Student.objects.prefetch_related(
        Prefetch("response_set", queryset=Response.objects.select_related())
    )
    .order_by("user__username")
    .all()
):
    data.append((s.user.username, s.user.last_name, str(s.final_score())))

#! EDIT HERE: scores.csv 的导出路径
Path("scores.csv").write_text("\n".join(map(",".join, data)), encoding="utf-8")
```

然后进一步计算每连情况。

```python
"""计算每连情况"""

from pathlib import Path

import polars as pl

# 1. Load data and verify

#! EDIT HERE: scores.csv 的路径，由上一步导出
scores_path = next(Path.cwd().glob("scores*.csv"))
print(f"分析“{scores_path}”。")

scores = pl.scan_csv(
    scores_path,
    schema={"id": pl.Utf8, "name": pl.Utf8, "score": pl.Int16},
)

people = (
    pl.read_excel(
        #! EDIT HERE: 学生名单的路径，由学工部提供
        Path("2024-08-20军训学生分连队.xlsx"),
        read_csv_options={
            #! EDIT HERE: 按顺序记录名单格式，多余的列可在后面 drop
            "schema": {"序号": pl.Utf8, "id": pl.Utf8, "name": pl.Utf8, "连队": pl.Utf8}
        },
    )
    .drop("序号")
    # 解析 "1连" → 1
    .with_columns(pl.col("连队").str.strip_suffix("连").cast(pl.Int16))
    .join(scores.collect(), on="id", how="outer")
)

print("名单没有的同学：", people.filter(pl.col("name").is_null()).sort("id"))

inconsistent = people.filter(
    pl.col("name").is_not_null()
    & pl.col("name_right").is_not_null()
    & (pl.col("name") != pl.col("name_right"))
)
assert inconsistent.is_empty(), inconsistent

people = (
    people.lazy()
    .with_columns(pl.col("name").fill_null(pl.col("name_right")))
    .drop("name_right")
    .filter(pl.col("连队").is_not_null())
    .collect()
)

print("名单中同学：", people.describe())

# 2. Aggregate

q = (
    people.lazy()
    #! EDIT HERE: 若分了营团，可考虑改为 group_by("营团", "连队") 和 sort("营团", "连队")
    .group_by("连队")
    .agg(
        pl.count().alias("应参与人数"),
        (pl.col("score") > 0).sum().alias("实际参与人数"),
        #! EDIT HERE: 需要统计的数据
        (pl.col("score").fill_null(0) > 0).mean().alias("参与率"),
        pl.col("score").fill_null(0).sum().alias("总得分"),
        pl.col("score").fill_null(0).mean().alias("均分"),
        pl.col("score").filter(pl.col("score") > 0).mean().alias("有成绩学生平均分"),
    )
    .sort("连队")
    .with_columns(pl.col("连队").cast(pl.Utf8) + "连")
)
df = q.collect()
print("各连情况：", df.describe())
#! EDIT HERE: 统计结果的导出路径
agg_path = scores_path.with_name(f"{scores_path.stem}-agg.xlsx")
df.write_excel(agg_path, column_formats={"答题比例": "0.00%"})
print(f"已保存到“{agg_path}”。")
```
