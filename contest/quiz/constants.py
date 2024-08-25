"""常量

视图、模板中的所有常量。

为避免循环`import`，本模块尽量不引用其它模块。
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import NamedTuple


class PageMeta(NamedTuple):
    """页面的元数据

    用于 ROUTES。
    """

    title: str
    """标题用于`<title>`、`<h1>`等"""

    login_required: bool
    """是否仅在登录后显示"""

    reluctant: bool = False
    """是否仅位于此页时显示

    - `True`: 位于此页时显示，位于其它页时隐藏
    - `False`: 总显示
    """


@dataclass(frozen=True)
class ConstantsNamespace:
    """常量的命名空间

    为了避免修改，使用 dataclass 而非 dict。
    """

    N_QUESTIONS_PER_RESPONSE = {
        "B": 5,
        "R": 15,
    }
    """每套题各题型题数

    `quiz.models.Question.Category` ⇒ `int`，未列出的题型不出现。
    """

    SCORE = {
        "B": 5,
        "R": 5,
    }
    """每种题目的分值

    `quiz.models.Question.Category` ⇒ `float`，且覆盖所有`Category`。

    如更改总分，建议一同更改`admin.py`中`ScoreFilter`的`breakpoints`。
    """

    DEADLINE_DURATION = timedelta(seconds=300)
    """作答限时"""

    MAX_TRIES = 2
    """答题次数上限"""

    YEAR = 2024
    MONTH = 8

    ROUTES = {
        "quiz:index": PageMeta(title="主页", login_required=False),
        "quiz:contest": PageMeta(title="答题", login_required=True, reluctant=True),
        "quiz:info": PageMeta(title="历史成绩", login_required=True),
        "quiz:contest_review": PageMeta(title="回顾", login_required=True, reluctant=True),
    }

    @property
    def n_questions_per_response_total(self) -> int:
        """每套题总题数"""
        return sum(self.N_QUESTIONS_PER_RESPONSE.values())

    @property
    def score_total(self) -> float:
        """每套题总分"""
        return sum(
            self.SCORE[category] * n_questions
            for category, n_questions in self.N_QUESTIONS_PER_RESPONSE.items()
        )


constants = ConstantsNamespace()
