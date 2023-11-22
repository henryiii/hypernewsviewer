from __future__ import annotations

import math
import os
import time
import warnings
from itertools import accumulate, groupby
from pathlib import Path
from typing import Any

import attrs
import sqlalchemy
from flask import (
    Flask,
    abort,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.wrappers import Response

from hypernewsviewer.model.messages import URCMain, URCMessage

from .model.structure import AllForums, DBForums, connect_forums

app = Flask("hypernewsviewer")
total_msgs: int | None = None

DIR = Path().resolve()
HNFILES = os.environ.get("HNFILES", str(DIR.parent.joinpath("hnfiles")))
HNDATABASE = os.environ.get("HNDATABASE", None)

if HNFTSDATABASE := os.environ.get("HNFTSDATABASE", None):
    db_file = Path(HNFTSDATABASE).resolve()
    db_uri = f"sqlite:///file:{db_file}?mode=ro&uri=true"


DATA_ROOT = Path(HNFILES).resolve()
DB_ROOT = Path(HNDATABASE).resolve() if HNDATABASE else None

FULLTEXT = sqlalchemy.table(
    "fulltext",
    sqlalchemy.column("responses"),
    sqlalchemy.column("title"),
    sqlalchemy.column("date"),
    sqlalchemy.column("from_"),
    sqlalchemy.column("rank"),
)
FTS_QUERY = sqlalchemy.select(
    FULLTEXT.c.responses,
    FULLTEXT.c.title,
    FULLTEXT.c.date,
    FULLTEXT.c.from_,
    sqlalchemy.text("snippet(fulltext, 4, '<mark>', '</mark>', ' ... ', 64)"),
)


BASE_PATH = "/HyperNews/CMS"


@app.template_filter("absolute_url")
def absolute_url(s: str) -> str:
    if s.startswith(BASE_PATH):
        msg = f"Should not make absolute url from {s}, stripping"
        warnings.warn(msg, stacklevel=2)
        s = s[len(BASE_PATH) :]
    return f"{request.url_root}{BASE_PATH.strip('/')}/{s.lstrip('/')}"


def get_forums() -> AllForums | DBForums:
    forums = getattr(g, "_forums_ctx", None)
    if forums is None:
        # pylint: disable-next=protected-access
        g._forums = connect_forums(DATA_ROOT, DB_ROOT)
        # pylint: disable-next=protected-access,unnecessary-dunder-call
        forums = g._forums_ctx = g._forums.__enter__()
    return forums


def get_search_engine() -> sqlalchemy.engine.Engine:
    if getattr(g, "_search_engine", None) is None:
        # pylint: disable-next=protected-access
        g._search_engine = sqlalchemy.create_engine(db_uri, future=True)
    # pylint: disable-next=protected-access
    return g._search_engine


@app.teardown_appcontext
def close_connection(_exception: BaseException | None) -> None:
    forums = getattr(g, "_forums", None)
    if forums is not None:
        forums.__exit__(None, None, None)


@app.route(f"{BASE_PATH}/")
def reroute_base_path() -> Response:
    return redirect(url_for("home_page"))


@app.route("/HyperNews/CMSCVS/<path:path>")
def reroute_hypernews_classic(path: str) -> Response:
    return redirect(f"/HyperNews/CMS/{path}")


@app.route("/HyperNews/")
def reroute_hypernews() -> Response:
    return redirect(url_for("home_page"))


@app.route("/")
def render_home() -> str:
    return render_template("root_landing.html")


@app.route("/favicon.ico")
def favicon() -> Response:
    return send_from_directory("static", "favicon.ico")


@app.route(f"{BASE_PATH}/Icons/<path:path>")
def icons(path: str) -> Response:
    return send_from_directory("static", f"Icons/{path}")


def get_msg_or_none(parts: list[str]) -> URCMessage | URCMain | None:
    forum, *others = parts
    path = "/".join(others)
    forums = get_forums()
    try:
        return forums.get_msg(forum, path) if path else forums.get_forum(forum)
    except FileNotFoundError:
        return None


@app.route(f"{BASE_PATH}/get/AUX/<path:path>")
def attachments(path: str) -> Response:
    return send_from_directory("static", f"{DATA_ROOT}/AUX/{path}")


@app.route(f"{BASE_PATH}/get/<path:responses>")
def get(responses: str) -> str | Response:
    if responses.endswith((".html", ".htm")):
        responses, _ = responses.rsplit(".", maxsplit=1)
    responses = responses.strip("/")

    parts = responses.split("/")
    forum, *others = parts
    path = "/".join(others)
    forums = get_forums()

    next_in_thread = ([*parts, "1"]) if path else []
    try:
        next_response = (parts[:-1] + [str(int(parts[-1]) + 1)]) if path else []
    except ValueError:
        abort(404)

    direction = request.args.get("dir", default=None)
    if direction is not None:
        if direction == "next-in-thread":
            return redirect(url_for("get", responses="/".join(next_in_thread)))
        if direction == "nextResponse":
            return redirect(url_for("get", responses="/".join(next_response)))

    trail = accumulate(parts, lambda a, b: f"{a}/{b}")
    breadcrumbs = [
        {"name": part, "url": url_for("get", responses=spath)}
        for part, spath in zip(parts, trail)
    ]

    msg = get_msg_or_none(parts)
    if msg is None:
        return f"Unable to find message: {responses} at {DATA_ROOT}"

    has_next_in_thread = get_msg_or_none(next_in_thread) is not None if path else False
    has_next_response = get_msg_or_none(next_response) is not None if path else False

    body = forums.get_html(forum, path)

    replies: list[dict[str, Any]] = []
    for m in forums.get_msgs(forum, path):
        local_forum, *local_others = m.responses.lstrip("/").split("/")
        msgs = forums.get_msg_paths(local_forum, "/".join(local_others))
        entries = len(list(msgs))
        url = url_for("get", responses=m.responses)
        replies.append({"msg": m, "url": url, "entries": entries})

    return render_template(
        "msg.html",
        urc=msg,
        forum=forums.get_forum(forum),
        body=body or "",
        breadcrumbs=breadcrumbs,
        replies=replies,
        has_next_in_thread=has_next_in_thread,
        has_next_response=has_next_response,
    )


@app.route(f"{BASE_PATH}/view-member.pl")
def view_member() -> str:
    (answer,) = request.args
    forums = get_forums()
    member = forums.get_member(answer)

    member_dict = {k: v for k, v in attrs.asdict(member).items() if k != "password"}

    return render_template("member.html", member=member_dict)


@app.route(f"{BASE_PATH}/view-members.pl")
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


@app.route(f"{BASE_PATH}/top.pl")
def home_page() -> str:
    return render_template("top.html")


@app.route(f"{BASE_PATH}/index")
def index() -> str:
    forums = get_forums()
    all_forums = filter(None, forums.get_forums_iter())
    sorted_forums = sorted(all_forums, key=lambda x: x.last_mod or x.date, reverse=True)
    return render_template("index.html", forums=sorted_forums)


@app.route(f"{BASE_PATH}/cindex")
def cindex() -> str:
    forums = get_forums()
    categories = forums.get_categories()
    all_forums = filter(None, forums.get_forums_iter())
    sorted_forums = sorted(
        all_forums, key=lambda x: (categories[x.categories], x.last_mod or x.date)
    )

    grouped_forums = {
        a: list(b) for a, b in groupby(sorted_forums, lambda x: x.categories)
    }
    return render_template("cindex.html", groups=grouped_forums, categories=categories)


@app.route(f"{BASE_PATH}/search")
def search() -> str:
    if HNFTSDATABASE is None:
        return render_template(
            "search.html", results=[], info_msg="No database configured"
        )

    search_engine = get_search_engine()

    start = request.args.get("start", "2000-01-01")
    stop = request.args.get("stop", "2022-12-31")
    page = int(request.args.get("page", "1"))
    query = request.args.get("query", "") or request.args.get("q", "")
    if query:
        timer = time.perf_counter()
        q = FTS_QUERY.where(sqlalchemy.text("fulltext=:query"))
        needs_range = start > "2000-01-01" or stop < "2022-12-31"

        if needs_range:
            q = q.where(FULLTEXT.c.date.between(start, stop))
        q = q.order_by(FULLTEXT.c.rank).limit(50).offset((page - 1) * 50)

        with search_engine.connect() as con:
            results_iter = con.execute(q, {"query": query})
            results = list(results_iter)
        total_time = time.perf_counter() - timer
        info_msg = f"Displaying results for: {query!r} (max 50 per page, page {page}) (took {total_time:.3f}s)"

    else:
        info_msg = """
        Search for a forum post. See
        <a href="https://www.sqlite.org/fts5.html#full_text_query_syntax">SQLite FTS5</a>
        for details on the syntax. Please avoid very simple queries that might
        match large numbers of posts, as those might time out the response."""

        results = []

    return render_template(
        "search.html",
        results=results,
        info_msg=info_msg,
        query=query,
        page=page,
        start=start,
        stop=stop,
    )
