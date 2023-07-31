from dataclasses import dataclass
from datetime import timedelta


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
        "quiz:index": {"title": "主页", "scenario": "both"},
        "quiz:contest": {"title": "答题", "scenario": "logged_in"},
        "quiz:info": {"title": "个人中心", "scenario": "logged_in"},
        "logout": {"title": "登出", "scenario": "logged_in"},
        "login": {"title": "登录", "scenario": "logged_out"},
    }


constants = ConstantsNamespace()
