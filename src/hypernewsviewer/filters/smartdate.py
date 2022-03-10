from __future__ import annotations

from ..core import app


@app.template_filter()
def smartdate(date):
    """Convert a date to string"""
    return date.strftime("%b %-d, %Y")
