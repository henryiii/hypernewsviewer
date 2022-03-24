from __future__ import annotations

import math
import os
from itertools import accumulate, groupby
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.wrappers import Response

from .model.structure import AllForums, DBForums, connect_forums

app = Flask("hypernewsviewer")

DIR = Path(".").resolve()
HNFILES = os.environ.get("HNFILES", str(DIR.parent.joinpath("hnfiles")))
HNDATABASE = os.environ.get("HNDATABASE", None)

DATA_ROOT = Path(HNFILES).resolve()
DB_ROOT = Path(HNDATABASE).resolve() if HNDATABASE else None


def get_forums() -> AllForums | DBForums:
    forums = getattr(g, "_forums", None)
    if forums is None:
        # pylint: disable-next=protected-access,assigning-non-slot
        g._forums = connect_forums(DATA_ROOT, DB_ROOT)
        forums = g._forums.__enter__()  # pylint: disable=protected-access
    return forums


@app.teardown_appcontext
def close_connection(_exception: Exception | None) -> None:
    forums = getattr(g, "_forums", None)
    if forums is not None:
        forums.__exit__(None, None, None)


@app.route("/")
def reroute() -> Response:
    return redirect(url_for("top_page"))


@app.route("/favicon.ico")
def empty() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route("/get/<path:subpath>")
def list_view(subpath: str) -> str | Response:
    if subpath.endswith(".html"):
        subpath = subpath[:-5]
    elif subpath.endswith(".htm"):
        subpath = subpath[:-4]

    parts = subpath.split("/")

    direction = request.args.get("dir", default=None)
    if direction is not None:
        if direction == "next-in-thread":
            parts.append("1")
            return redirect(url_for("list_view", subpath="/".join(parts)))
        if direction == "nextResponse":
            parts[-1] = str(int(parts[-1]) + 1)
            return redirect(url_for("list_view", subpath="/".join(parts)))

    trail = accumulate(parts, lambda a, b: f"{a}/{b}")
    breadcrumbs = [
        {"name": part, "url": url_for("list_view", subpath=spath)}
        for part, spath in zip(parts, trail)
    ]
    forum, *others = parts
    path = "/".join(others)

    forums = get_forums()
    try:
        msg = forums.get_msg(forum, path) if path else forums.get_forum(forum)
    except FileNotFoundError:
        return f"Unable to find message: {subpath} at {DATA_ROOT}"

    body = forums.get_html(
        forum, path if others else (path + "/" + path.rsplit("/", 1)[-1])
    )

    replies: list[dict[str, Any]] = []
    print(forum, path)
    for m in forums.get_msgs(forum, path):
        local_forum, *local_others = m.responses.lstrip("/").split("/")
        msgs = forums.get_msg_paths(local_forum, "/".join(local_others))
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
    forums = get_forums()
    member = forums.get_member(answer)

    header = """<p><a href="/">home</a></p>\n"""
    return header + "<br/>\n".join(
        f"{k}: {v}" for k, v in member.as_simple_dict().items() if k != "password"
    )


@app.route("/view-members.pl")
def view_members() -> str:
    RESULTS_PER_PAGE = 50
    find = request.args.get("find", default=None)
    page = request.args.get("page", default=1, type=int)
    forums = get_forums()
    members = forums.get_member_iter()

    # Simple find
    if find:
        find = find.strip("^").upper()
        members = (
            m
            for m in members
            if f" {find}" in m.name.upper() or m.email.upper().startswith(find)
        )

    sorted_members = sorted(members, key=lambda m: m.email)
    num_pages = math.ceil(len(sorted_members) / RESULTS_PER_PAGE)
    page = min(max(1, page), num_pages)
    limited_members = sorted_members[
        (page - 1) * RESULTS_PER_PAGE : page * RESULTS_PER_PAGE
    ]

    return render_template(
        "members.html",
        members=limited_members,
        page=page,
        num_pages=num_pages,
        find=find,
    )


@app.route("/top.pl")
def top_page() -> str:
    return render_template("top.html")


@app.route("/index")
def get_index() -> str:
    forums = get_forums()
    all_forums = filter(None, forums.get_forums_iter())
    sorted_forums = sorted(all_forums, key=lambda x: x.last_mod or x.date, reverse=True)
    return render_template("index.html", forums=sorted_forums)


@app.route("/cindex")
def get_cindex() -> str:
    forums = get_forums()
    categories = forums.get_categories()
    all_forums = filter(None, forums.get_forums_iter())
    sorted_forums = sorted(
        all_forums, key=lambda x: (x.categories, x.last_mod or x.date)
    )

    grouped_forums = {
        a: list(b) for a, b in groupby(sorted_forums, lambda x: x.categories)
    }
    return render_template("cindex.html", groups=grouped_forums, categories=categories)
