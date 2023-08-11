"""常量

视图、模板中的所有常量。
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
        "quiz:contest": PageMeta(title="答题", login_required=True, reluctant=True),
        "quiz:info": PageMeta(title="个人中心", login_required=True),
    }


constants = ConstantsNamespace()
