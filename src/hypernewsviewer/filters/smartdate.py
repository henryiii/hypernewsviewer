from __future__ import annotations

import datetime

from ..core import app


@app.template_filter()  # type: ignore[misc]
def smartdate(date: datetime.datetime) -> str:
    """Convert a date to string"""
    return date.strftime("%b %-d, %Y")
