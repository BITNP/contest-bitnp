"""Database → Simple Markdown

Examples:
```
$ just manage dump_md > ./fixtures/题库.md
```
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.base import BaseCommand

if TYPE_CHECKING:
    from typing import Generator

from typing import TYPE_CHECKING

from quiz.models import Question

_PREFIX = {
    True: "【应选】",
    False: "",
}


def _dump() -> Generator[str, None, None]:
    for q in Question.objects.all():
        yield f"# {q.content}\n\n"
        yield "\n\n".join(_PREFIX[c.correct] + c.content for c in q.choice_set.all())
        yield "\n\n"


class Command(BaseCommand):
    help = """Database → Simple Markdown"""

    def handle(self, *_args, **_options) -> None:
        """The actual logic"""
        self.stdout.write("".join(_dump()))
