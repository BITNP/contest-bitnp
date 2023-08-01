from dataclasses import dataclass
from datetime import timedelta
from typing import NamedTuple


class PageMeta(NamedTuple):
    title: str
    """标题用于`<title>`、`<h1>`等"""

    login_required: bool
    """是否仅在登录后显示"""


@dataclass(frozen=True)
class ConstantsNamespace:
    DEADLINE_DURATION = timedelta(minutes=15)
    """作答限时"""

    N_QUESTIONS_PER_RESPONSE = 3
    """每套题的题数"""

    MAX_TRIES = 100
    """答题次数上限"""

    YEAR = 2023
    MONTH = 9

    SCORE = 100
    """一套题的总分"""

    ROUTES = {
        "quiz:index": PageMeta(title="主页", login_required=False),
        "quiz:contest": PageMeta(title="答题", login_required=True),
        "quiz:info": PageMeta(title="个人中心", login_required=True),
    }


constants = ConstantsNamespace()
