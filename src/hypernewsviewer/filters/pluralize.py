from __future__ import annotations

import inflection

from ..core import app


@app.template_filter()  # type: ignore[misc]
def pluralize(num: int, text: str) -> str:
    """Pluralize based on a number"""
    if num == 1:
        return f"{num} {text}"
    return f"{num} {inflection.pluralize(text)}"
