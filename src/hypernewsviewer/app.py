from __future__ import annotations

from functools import lru_cache
from itertools import accumulate
from pathlib import Path
from typing import Any

from flask import Flask, redirect, render_template, send_from_directory, url_for
from werkzeug.wrappers import Response

from .model.structure import (
    get_any_urc,
    get_html,
    get_msg_paths,
    get_msgs,
)

app = Flask("hypernewsviewer")

DIR = Path('.').resolve()
DATA_ROOT = DIR.parent.joinpath("hnfiles").resolve()

@app.route("/")
def reroute() -> Response:
    return redirect(url_for("list_view", subpath="hnTest"))


@app.route("/favicon.ico")
def empty() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route("/<path:subpath>")
@lru_cache
def list_view(subpath: str) -> str:
    rootpath = DATA_ROOT / subpath

    parts = subpath.split("/")
    trail = accumulate(parts, lambda a, b: f"{a}/{b}")
    breadcrumbs = [
        {"name": part, "url": url_for("list_view", subpath=spath)}
        for part, spath in zip(parts, trail)
    ]

    urc = get_any_urc(rootpath)
    if len(breadcrumbs) > 1:
        body = get_html(rootpath)
    else:
        body = get_html(rootpath / rootpath.name)

    replies: list[dict[str, Any]] = []
    for m in get_msgs(rootpath):
        msgs = get_msg_paths(DATA_ROOT / m.responses.lstrip("/"))
        entries = len(list(msgs))
        url = url_for("list_view", subpath=m.responses)
        replies.append({"msg": m, "url": url, "entries": entries})

    return render_template(
        "msg.html",
        urc=urc,
        forum_title="HyperNews Test Forum",
        body=body or "",
        breadcrumbs=breadcrumbs,
        replies=replies,
    )
