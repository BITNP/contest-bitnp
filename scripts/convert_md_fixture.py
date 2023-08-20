"""Simple Markdown → YAML fixture

Examples:
```
$ python ./scripts/convert_md_fixture.py ./fixtures/NGE.md
```

"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from itertools import count
from pathlib import Path

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
args = parser.parse_args()

src_file = args.source

questions_count = count()
choices_count = count()
last_question_pk = 0
is_first_choice = True
data = []

for line in src_file.read_text(encoding="UTF-8").splitlines():
    line = line.strip()
    if not line:  # empty
        continue
    elif line.startswith("# "):
        last_question_pk = next(questions_count)
        data.append(
            {
                "model": "quiz.question",
                "pk": last_question_pk,
                "fields": {"content": line.removeprefix("# ")},
            }
        )

        is_first_choice = True
    else:
        data.append(
            {
                "model": "quiz.choice",
                "pk": next(choices_count),
                "fields": {
                    "content": line,
                    "correct": is_first_choice,
                    "question": last_question_pk,
                },
            }
        )
        is_first_choice = False

dst_file = src_file.with_suffix(".yaml")
dst_file.write_text(dump(data, Dumper=SafeDumper), encoding="utf-8")
print(dst_file)
