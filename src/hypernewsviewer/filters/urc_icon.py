from __future__ import annotations

from flask import url_for

from ..core import app
from ..model.enums import UpRelType


@app.template_filter()  # type: ignore[misc]
def urc_icon(icon: UpRelType) -> str:
    return url_for("icons", path=_compute_icon(icon))


def _compute_icon(icon: UpRelType) -> str:
    """Convert an enum to an icon link"""
    if icon in {UpRelType.Default, UpRelType.None_}:
        return "hnsmall.gif"
    if icon == UpRelType.News:
        return "news.gif"
    if icon == UpRelType.Warning:
        return "warning.gif"
    if icon == UpRelType.Feedback:
        return "feedback.gif"
    if icon == UpRelType.Question:
        return "question.gif"
    if icon == UpRelType.More:
        return "more.gif"
    if icon == UpRelType.Disagree:
        return "disagree.gif"
    if icon == UpRelType.Note:
        return "note.gif"
    if icon == UpRelType.Ok:
        return "ok.gif"
    if icon == UpRelType.Angry:
        return "angry.gif"
    if icon == UpRelType.Agree:
        return "agree.gif"
    if icon == UpRelType.Idea:
        return "idea.gif"
    if icon == UpRelType.Sad:
        return "sad.gif"

    return "hnsmall.gif"
