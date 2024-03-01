# 导出

```shell
$ poetry install --with agg
```

## 流程

在`just shell`中运行以下内容，定稿所有超期答卷。

```shell
from quiz.models import DraftResponse
from quiz.views import continue_or_finalize

for r in DraftResponse.objects.all():
    print(continue_or_finalize(r))
```

利用`just manage dumpdata`和`just manage loaddata`，将数据复制到本地。（数据量大，而服务器资源有限）

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

Path("scores.csv").write_text("\n".join(map(",".join, data)), encoding="utf-8")
```

然后进一步计算每连情况。

```python
"""计算每连情况"""
from pathlib import Path

import polars as pl

# 1. Load data and verify

scores_path = next(Path(__file__).parent.glob("scores*.csv"))
print(f"分析“{scores_path}”。")

scores = pl.scan_csv(
    scores_path,
    schema={"id": pl.Utf8, "name": pl.Utf8, "score": pl.Int16},
)

people = pl.read_excel(
    Path("D:/大学/Clubs/NetPioneer_2022_2023/技术保障中心/国防知识竞赛/连队人员信息0830.xlsx"),
    read_csv_options={
        "schema": {"营团": pl.Utf8, "连队": pl.Int64, "id": pl.Utf8, "name": pl.Utf8}
    },
).join(scores.collect(), on="id", how="outer")

print("名单没有的同学：", people.filter(pl.col("name").is_null()))

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
    .filter(pl.col("营团").is_not_null() & pl.col("连队").is_not_null())
    .collect()
)

print("名单中同学：", people.describe())

# 2. Aggregate

q = (
    people.lazy()
    .group_by("营团", "连队")
    .agg(
        pl.count().alias("总人数"),
        pl.col("score").fill_null(0).mean().alias("平均分"),
        (pl.col("score") > 0).sum().alias("答题人数"),
    )
    .with_columns((pl.col("答题人数") / pl.col("总人数")).alias("答题比例"))
    .sort("营团", "连队")
)
df = q.collect()
print("各连情况：", df.describe())
agg_path = scores_path.with_name(f"{scores_path.stem}-agg.xlsx")
df.write_excel(agg_path, column_formats={"答题比例": "0.00%"})
print(f"已保存到“{agg_path}”。")
```
