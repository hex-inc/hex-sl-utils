from __future__ import annotations

from typing import Literal


# Type alias for time truncation units
TruncUnit = Literal[
    "year",
    "quarter",
    "month",
    "week",
    "weekmonday",
    "day",
    "hour",
    "minute",
    "second",
    "millisecond",
]
