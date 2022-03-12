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
    AllForums,
    get_categories,
    get_forums,
    get_member,
    get_msg_paths,
)

app = Flask("hypernewsviewer")

DIR = Path(".").resolve()
HNFILES = os.environ.get("HNFILES", str(DIR.parent.joinpath("hnfiles")))
DATA_ROOT = Path(HNFILES).resolve()
FORUMS = AllForums(root=DATA_ROOT)


@app.route("/")
def reroute() -> Response:
    return redirect(url_for("top_page"))


@app.route("/favicon.ico")
def empty() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route("/get/<path:subpath>")
def list_view(subpath: str) -> str:
    if subpath.endswith(".html"):
        subpath = subpath[:-5]
    elif subpath.endswith(".htm"):
        subpath = subpath[:-4]

    parts = subpath.split("/")
    trail = accumulate(parts, lambda a, b: f"{a}/{b}")
    breadcrumbs = [
        {"name": part, "url": url_for("list_view", subpath=spath)}
        for part, spath in zip(parts, trail)
    ]
    forum_name, *others = parts
    path = Path("/".join(others))

    try:
        forum = FORUMS.get_forum(forum_name)
    except FileNotFoundError:
        return f"Unable to find forum: {subpath} at {DATA_ROOT}"

    try:
        msg = forum.get_msg(path)
    except FileNotFoundError:
        return f"Unable to find message: {subpath} at {DATA_ROOT}"

    if others:
        body = forum.get_html(path)
    else:
        body = forum.get_html(path / path.name)

    replies: list[dict[str, Any]] = []
    for _, m in forum.get_msgs(path):
        msgs = get_msg_paths(DATA_ROOT / m.responses.lstrip("/"))
        entries = len(list(msgs))
        url = url_for("list_view", subpath=m.responses)
        replies.append({"msg": m, "url": url, "entries": entries})

    return render_template(
        "msg.html",
        urc=msg,
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
