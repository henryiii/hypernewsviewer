import inflection

from ..app import app


@app.template_filter()
def pluralize(num, text):
    """Pluralize based on a number"""
    if num == 1:
        return f"{num} {text}"
    else:
        return f"{num} {inflection.pluralize(text)}"
