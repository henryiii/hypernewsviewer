from __future__ import annotations

from itertools import accumulate
from pathlib import Path

from flask import Flask, redirect, url_for
from markupsafe import escape
from werkzeug.wrappers import Response

from hypernewsviewer.model.structure import get_html, get_msg_paths, get_msgs

app = Flask("hypernewsviewer")

DIR = Path(__file__).parent.resolve()
DATA_ROOT = DIR.parent.joinpath("hnfiles").resolve()


@app.route("/")
def hello_world() -> Response:
    return redirect(url_for("list_view", subpath="hnTest"))


@app.route("/<path:subpath>/list")
def list_view(subpath: str) -> str:
    rootpath = DATA_ROOT / subpath

    output = ""

    if rootpath.stem.isdigit():
        parts = subpath.split("/")
        trail = accumulate(parts, lambda a, b: f"{a}/{b}")
        for part, spath in zip(parts, trail):
            back_url = url_for("list_view", subpath=spath)
            output += fr'<a href="{back_url}">{part}</a> / '

        output += "</p>\n"

    html = get_html(rootpath)
    if html is not None:
        output += html

    for m in get_msgs(rootpath):
        msgs = get_msg_paths(DATA_ROOT / m.responses.lstrip("/"))
        entries = len(list(msgs))
        url = url_for("list_view", subpath=m.responses)
        rep_txt = "replies" if entries > 1 else "reply"
        replies = f" ({entries} {rep_txt})" if entries else ""
        output += (
            fr'{str(m.num)}: <a href="{url}"> {escape(m.title)}</a>{replies}</p>'
        )

    return output
