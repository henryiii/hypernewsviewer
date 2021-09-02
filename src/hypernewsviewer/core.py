import os
from functools import lru_cache
from itertools import accumulate
from pathlib import Path
from typing import Any, Dict, List

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.wrappers import Response

from .model.structure import get_any_urc, get_html, get_member, get_msg_paths, get_msgs

app = Flask("hypernewsviewer")

DIR = Path(".").resolve()
HNFILES = os.environ.get("HNFILES", str(DIR.parent.joinpath("hnfiles")))
DATA_ROOT = Path(HNFILES).resolve()


@app.route("/")
def reroute() -> Response:
    return redirect(url_for("list_view", subpath="hnTest"))


@app.route("/favicon.ico")
def empty() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route("/get/<path:subpath>")
@lru_cache()
def list_view(subpath: str) -> str:
    rootpath = DATA_ROOT / subpath

    parts = subpath.split("/")
    trail = accumulate(parts, lambda a, b: f"{a}/{b}")
    breadcrumbs = [
        {"name": part, "url": url_for("list_view", subpath=spath)}
        for part, spath in zip(parts, trail)
    ]

    try:
        urc = get_any_urc(rootpath)
    except FileNotFoundError:
        return f"Unable to find forum: {subpath}"
    if len(breadcrumbs) > 1:
        body = get_html(rootpath)
    else:
        body = get_html(rootpath / rootpath.name)

    replies: List[Dict[str, Any]] = []
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


@app.route("/view-member.pl")
@lru_cache()
def view_member() -> str:
    (answer,) = request.args
    rootpath = DATA_ROOT / "hnpeople" / answer
    member = get_member(rootpath)

    header = """<p><a href="/">home</a></p>\n"""
    return header + "<br/>\n".join(
        f"{k}: {v}" for k, v in member.as_simple_dict().items() if k != "password"
    )
