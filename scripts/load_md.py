"""Simple Markdown → YAML fixture

Examples:
```
$ python ./scripts/load_md.py ./fixtures/题库.md
```
"""

from __future__ import annotations

import re
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from collections import deque
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING
from warnings import warn

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator

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
        "--pk-shift",
        type=int,
        help="数据 ID 偏移量，用于避免与现有数据重复，默认为 0",
        default=0,
    )
    return parser


@dataclass
class Choice:
    """选项"""

    content: str
    correct: bool


def dump_objects(
    question_content: str, choices: list[Choice], question_pk: int
) -> Generator[dict[str, str | int | dict], None, None]:
    """Dump objects into YAML fixture format"""
    # 1. Validate and normalize
    if all(c.content in ["正确", "错误"] for c in choices):
        category = "B"
        assert len(choices) == 2, f"判断题选项不正常：{choices}"  # noqa: PLR2004
    else:
        category = "R"

    assert len([c for c in choices if c.correct]) == 1, (
        f"正确选项应当只有一个，可能忘了用“# ”分隔题目：{choices}"
    )

    assert len(choices) > 1, f"选项不应只有一个：{choices}"

    if re.search(R"\b[ABCD]\b", question_content):
        warn(f"题干可能包含答案：{question_content}", stacklevel=1)

    if re.search(R"[,?!]", question_content):
        warn(f"题干包含半角标点：{question_content}", stacklevel=1)

    if re.search(R"['\"]", question_content):
        warn(f"题干包含直引号，建议改用上下引号：{question_content}", stacklevel=1)

    question_content = re.sub(R"[\s　]*[（\(][\s　]*[）\)][\s　]*", "（ ）", question_content)

    if category == "B" and "（ ）" in question_content:
        warn(f"判断题设了空：{question_content}", stacklevel=1)

    # 2. Dump
    yield {
        "model": "quiz.question",
        "pk": question_pk,
        "fields": {
            "content": question_content,
            "category": category,
        },
    }
    for c in choices:
        yield {
            "model": "quiz.choice",
            "fields": {
                "content": c.content,
                "correct": c.correct,
                "question": question_pk,
            },
        }


def parse_choice(line: str) -> Choice:
    """解析`Choice`"""
    if line.startswith("【应选】"):
        return Choice(
            correct=True,
            content=line.removeprefix("【应选】").strip(),
        )
    else:
        return Choice(correct=False, content=line)


def read_to_next_question(lines: Iterator[str]) -> tuple[list[Choice], str | None]:
    """Read lines until the next question

    Returns:
        (choices, next_question)
    """
    choices: list[Choice] = []

    while True:
        try:
            line = next(lines).strip()
        except StopIteration:
            return (choices, None)

        if not line:  # empty
            continue

        if line.startswith("# "):  # question
            return (choices, line.removeprefix("# ").strip())

        choices.append(parse_choice(line))


def load(lines: Iterator[str], *, pk_shift: int) -> deque[dict]:
    """Simple Markdown → A list of records"""
    questions_count = count(start=pk_shift)

    records: deque[dict] = deque()

    _choices, last_question = read_to_next_question(lines)
    assert len(_choices) == 0

    while True:
        if last_question is None:
            return records

        choices, next_question = read_to_next_question(lines)
        records.extend(
            dump_objects(
                question_content=last_question,
                choices=choices,
                question_pk=next(questions_count),
            )
        )

        last_question = next_question


def main() -> None:
    """Main function"""
    args = build_parser().parse_args()
    src_file = args.source

    data = load(
        iter(src_file.read_text(encoding="UTF-8").splitlines()),
        pk_shift=args.pk_shift,
    )
    dst_file = src_file.with_suffix(".yaml")
    dst_file.write_text(
        dump(list(data), Dumper=SafeDumper, allow_unicode=True), encoding="utf-8"
    )
    print(dst_file)


if __name__ == "__main__":
    main()
