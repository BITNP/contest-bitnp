# 监控可能需要的命令

## 进入服务器上的 Django shell

```shell
$ ssh …
$ podman exec -it contest_web_1 bash
/usr/src/app $ python manage.py shell
>>> …
```

## 每 10 min 获取一次答题人数、登录人数，存入`records.csv`，持续 2 h

```powershell
> 1..12 | % { sleep -Seconds 600; .\records.ps1 | tee -a .\records.csv }
2023-08-31T15:34:26.898815+00:00, 0, 26
…
```

`records.ps1`:

```powershell
ssh NP "podman exec contest_web_1 python manage.py shell --command `"from quiz.models import Student, Response; from django.utils import timezone; print(timezone.now().isoformat(), len(set(Response.objects.filter(student__user__username__startswith='112023').values_list('student__user__username'))), Student.objects.filter(user__username__startswith='112023').count(), sep=', ')`""
```

`records.csv`:

```csv
at, n_responded, n_logged_in
2023-08-29T16:09:00.000000+00:00, 0, 2
2023-08-31T09:06:00.000000+00:00, 0, 10
…
```

`records.py`:

```python
"""人数随时刻变化的图象"""
from pathlib import Path

import polars as pl
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
from matplotlib.pyplot import show, subplots

records = (
    pl.scan_csv(
        Path(__file__).parent / "records.csv",
        schema={"at": pl.Datetime, "n_responded": pl.Int64, "n_logged_in": pl.Int64},
    )
    .with_columns(
        pl.col("at").dt.replace_time_zone("UTC").dt.convert_time_zone("Asia/Shanghai")
    )
    .collect()
)
print(records)

fig, ax = subplots()

ax.plot("at", "n_responded", data=records, label="答题", marker="+")
ax.plot("at", "n_logged_in", data=records, label="登录", marker="+")

ax.set_xlabel("时刻")
ax.set_ylabel("人数")
ax.grid(True)
ax.legend()

locator = AutoDateLocator()
formatter = ConciseDateFormatter(locator, tz="Asia/Shanghai")
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(formatter)

show()
```

## 指定学号，找到最后一次答题记录

（这样比 admin 网页快）

```python
>>> from quiz.models import Student
>>> Student.objects.get(user__username='112023○○').response_set.order_by('-submit_at')[0].answer_set.all()
<QuerySet [<Answer: “我国兵役法的核心内容是兵役制度（判断）” → “正确”>, …]>
```

## 删除奇异`User`

```python
>>> from quiz.models import User
>>> User.objects.filter(student__isnull=True, username__startswith='112023').count()
>>> User.objects.filter(student__isnull=True, username__startswith='112023').delete()
```

## 零分答卷数量

消耗大，请避免使用。

```python
>>> from quiz.models import Response
>>> len(set(r.student.user.username for r in Response.objects.all() if r.score() == 0))
```

## 删除奇异答卷

消耗大，请避免使用。

```python
"""删除奇异答卷"""

from quiz.models import Response

for r in reversed(Response.objects.all().select_related()):
    s = r.score()
    c = r.answer_set.filter(choice__isnull=True).count()
    if s == 0 or s < 60 and c >= 3:
        print(r, "分数 =", s, "没选数量 =", c)
        r.delete()
```

## 删除指定同学（及其答卷等数据）

从未实际测试过。

```python
"""删除同学

从 Excel 手动复制粘贴，学号每行一个
"""
from pathlib import Path

from quiz.models import Student

usernames: list[str] = Path('file.txt').read_text().splitlines()

for name in usernames:
    s = Student.objects.get(user__username=name)
    print(s)
    s.delete()
```

## 找出同步失败的答卷

消耗大，请避免使用。

```python
from quiz.models import Student

n = 1
for student in Student.objects.all():
    c = student.response_set.count()
    if c >= 3:
        for r in student.response_set.all():
            print(r.score(), r.submit_at)
        n += 1
        print("#", n, end="\n\n")
```
