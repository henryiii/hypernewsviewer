from __future__ import annotations

import os
from itertools import accumulate, groupby
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.wrappers import Response

from .model.structure import (
    get_any_urc,
    get_categories,
    get_forums,
    get_html,
    get_member,
    get_msg_paths,
    get_msgs,
)

app = Flask("hypernewsviewer")

DIR = Path(".").resolve()
HNFILES = os.environ.get("HNFILES", str(DIR.parent.joinpath("hnfiles")))
DATA_ROOT = Path(HNFILES).resolve()


@app.route("/")
def reroute() -> Response:
    return redirect(url_for("top_page"))


@app.route("/favicon.ico")
def empty() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route("/get/<path:subpath>")
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
        return f"Unable to find forum: {subpath} at {DATA_ROOT}"
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


@app.route("/view-member.pl")
def view_member() -> str:
    (answer,) = request.args
    rootpath = DATA_ROOT / "hnpeople" / answer
    member = get_member(rootpath)

    header = """<p><a href="/">home</a></p>\n"""
    return header + "<br/>\n".join(
        f"{k}: {v}" for k, v in member.as_simple_dict().items() if k != "password"
    )


@app.route("/top.pl")
def top_page() -> str:
    return render_template("top.html")


@app.route("/index")
def get_index() -> str:
    forums = get_forums(DATA_ROOT)
    sorted_forums = sorted(forums, key=lambda x: x.last_mod, reverse=True)
    return render_template("index.html", forums=sorted_forums)


@app.route("/cindex")
def get_cindex() -> str:
    categories = get_categories(DATA_ROOT / "CATEGORIES")
    forums = get_forums(DATA_ROOT)
    sorted_forums = sorted(forums, key=lambda x: (x.categories, x.last_mod))
    grouped_forums = {
        a: list(b) for a, b in groupby(sorted_forums, lambda x: x.categories)
    }
    return render_template("cindex.html", groups=grouped_forums, categories=categories)
