"""PHP旧项目导出的数据 → YAML fixture

Examples:
```
$ cat ./fixtures/problems.csv
id,type,description,answer,choices
"1","1","题干","0","选项||啊||噫||嘻"
"205","0","《联合国海洋法公约》规定专属经济区为300海里。","1",NULL
…

$ python ./scripts/load_problems_csv.py ./fixtures/problems.csv
```

"""
from __future__ import annotations

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections import deque
from csv import DictReader
from pathlib import Path
from warnings import warn

# 参考`django.core.serializers.pyyaml`。
# https://github.com/django/django/blob/9946f0b0d9356b55e819f861b31615fa5b548f99/django/core/serializers/pyyaml.py
from yaml import dump

# Use the C (faster) implementation if possible
try:
    from yaml import CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeDumper  # type: ignore[assignment]


parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("source", type=Path, help="源文件")
parser.add_argument(
    "--pk-shift",
    type=int,
    help="数据 ID 偏移量，用于避免与现有数据重复，默认为 0",
    default=0,
)
args = parser.parse_args()

src_file: Path = args.source
pk_shift: int = args.pk_shift

data: deque[dict] = deque()
with src_file.open(encoding="utf-8") as f:
    reader = DictReader(f)
    for row in reader:
        # Convert
        question_pk = pk_shift + int(row["id"])

        if row["choices"] in ["NULL", ""]:  # 判断题
            if row["type"] != "0":
                warn(
                    "type 和 choies 不一致，将当作判断题："
                    f"“{row['description']}” → “{row['choices']}”",
                    stacklevel=1,
                )
            category = "B"
            choices = ["正确", "错误"]
        else:  # 单项选择题
            if row["type"] != "1":
                warn(
                    "type 和 choies 不一致，将当作单项选择题："
                    f"“{row['description']}” → “{row['choices']}”",
                    stacklevel=1,
                )
            category = "R"
            choices = row["choices"].split("||")

        # Save
        data.append(
            {
                "model": "quiz.question",
                "pk": question_pk,
                "fields": {
                    "content": row["description"],
                    "category": category,
                },
            }
        )

        for i, c in enumerate(choices):
            data.append(
                {
                    "model": "quiz.choice",
                    "fields": {
                        "content": c,
                        "correct": i == int(row["answer"]),
                        "question": question_pk,
                    },
                }
            )

dst_file = src_file.with_suffix(".yaml")
dst_file.write_text(dump(list(data), Dumper=SafeDumper, allow_unicode=True), encoding="utf-8")
print(f"Output: {dst_file}")
