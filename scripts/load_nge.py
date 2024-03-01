"""Simple Markdown → YAML fixture

Examples:
```
$ python ./scripts/load_nge.py ./fixtures/NGE.md --first-correct
```

"""

from __future__ import annotations

from argparse import ArgumentParser, BooleanOptionalAction, RawDescriptionHelpFormatter
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

# 参考`django.core.serializers.pyyaml`。
# https://github.com/django/django/blob/9946f0b0d9356b55e819f861b31615fa5b548f99/django/core/serializers/pyyaml.py
from yaml import dump

# Use the C (faster) implementation if possible
try:
    from yaml import CSafeDumper as SafeDumper
except ImportError:
    from yaml import SafeDumper  # type: ignore[assignment]


def build_parser() -> ArgumentParser:
    """Build the CLI parser"""
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="源文件")
    parser.add_argument(
        "--first-correct",
        help="是否认为首个选项正确",
        action=BooleanOptionalAction,
        default=False,
    )
    return parser


def load(lines: Iterable[str], *, assume_first_choice_is_correct: bool = False) -> list[dict]:
    """Simple Markdown → A list of records"""
    questions_count = count()
    choices_count = count()
    last_question_pk = 0
    is_first_choice = True
    data = []

    for line in lines:
        line = line.strip()  # noqa: PLW2901 redefined-loop-name
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
            if assume_first_choice_is_correct:
                correct = is_first_choice
            else:
                raise NotImplementedError

            data.append(
                {
                    "model": "quiz.choice",
                    "pk": next(choices_count),
                    "fields": {
                        "content": line,
                        "correct": correct,
                        "question": last_question_pk,
                    },
                }
            )
            is_first_choice = False

    return data


def main() -> None:
    """Main function"""
    args = build_parser().parse_args()
    src_file = args.source

    data = load(
        src_file.read_text(encoding="UTF-8").splitlines(),
        assume_first_choice_is_correct=args.first_correct,
    )
    dst_file = src_file.with_suffix(".yaml")
    dst_file.write_text(dump(data, Dumper=SafeDumper), encoding="utf-8")
    print(dst_file)


if __name__ == "__main__":
    main()
