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

    # todo: Not used in models
    SCORE = 100


constants = ConstantsNamespace()
