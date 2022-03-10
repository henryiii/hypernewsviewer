from __future__ import annotations

import inflection

from ..core import app


@app.template_filter()
def pluralize(num, text):
    """Pluralize based on a number"""
    if num == 1:
        return f"{num} {text}"
    else:
        return f"{num} {inflection.pluralize(text)}"
