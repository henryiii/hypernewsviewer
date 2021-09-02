from functools import partial

from hypernewsviewer.app import app

application = partial(app, debug=True)

__all__ = ("application",)
