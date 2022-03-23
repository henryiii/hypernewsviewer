# pylint: disable=cell-var-from-loop
from __future__ import annotations

import contextlib
import functools
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Callable, Generator, Iterable, TypeVar

import click
import rich.console
import rich.live
import rich.logging
import rich.progress
import rich.traceback
from bs4 import BeautifulSoup
from rich import print  # pylint: disable=redefined-builtin
from rich.progress import Progress
from rich.table import Table
from rich.tree import Tree

from .cliutils import get_html_panel, walk_tree
from .messages import Member, Message, URCMain
from .structure import AllForums, DBForums, connect_forums

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec

# pylint: disable=redefined-outer-name

rich.traceback.install(suppress=[click, rich], show_locals=True, width=None)

T = TypeVar("T")
P = ParamSpec("P")

logging.basicConfig(
    level=logging.NOTSET,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[rich.logging.RichHandler(rich_tracebacks=True)],
)

log_sql = logging.getLogger("hypernewsviewer.sql")
log_sql.setLevel(logging.INFO)

DIR = Path(__file__).parent.resolve()


@contextlib.contextmanager
def timer(description: str) -> Generator[None, None, None]:
    start = time.monotonic()
    try:
        yield
    finally:
        ellapsed_time = time.monotonic() - start
        print(f"{description}: {ellapsed_time}")


PROGRESS_COLUMNS = (
    "[green][progress.description]{task.description}",
    rich.progress.BarColumn(bar_width=None),
    "[green]{task.completed} of {task.total:g}",
    "[progress.percentage]{task.percentage:>3.0f}%",
    rich.progress.TimeElapsedColumn(),
    rich.progress.TimeRemainingColumn(),
)


def track(
    iterable: Iterable[T], total: int, description: str
) -> Generator[T, None, None]:
    """
    Track progress of an iterable using the custom progress bar.
    """
    with Progress(*PROGRESS_COLUMNS, expand=True) as p:
        yield from p.track(iterable, total=total, description=description)


def convert_context(
    function: Callable[Concatenate[AllForums | DBForums, P], None]  # type: ignore[misc]
) -> Callable[P, None]:
    """
    Decorator to convert the context to a DBForums or AllForums object.
    """

    @functools.wraps(function)
    def wrapper(ctx: click.Context, *args: P.args, **kwargs: P.kwargs) -> None:
        with connect_forums(ctx.obj["root"], ctx.obj["db"]) as forums:
            function(forums, *args, **kwargs)

    return click.pass_context(wrapper)  # type: ignore[return-value]


@click.group(
    help="Run with a tree path (like hnTest/1).",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--root",
    type=click.Path(file_okay=False, path_type=Path),  # type: ignore[type-var]
    default=Path(
        os.environ.get("HNFILES", str(DIR.joinpath("../../../../hnfiles").resolve()))
    ),
    help="Set a different path for the data directory",
)
@click.option(
    "--db",
    default=Path(os.environ["HNDATABASE"]) if "HNDATABASE" in os.environ else None,
    type=click.Path(file_okay=True, path_type=Path),  # type: ignore[type-var]
    help="Path to the database",
)
@click.pass_context
def main(ctx: click.Context, root: Path, db: Path | None) -> None:
    ctx.ensure_object(dict)
    ctx.obj["db"] = db.resolve() if db else None
    ctx.obj["root"] = root.resolve()


@main.command("list", help="Show a table of messages.")
@convert_context
@click.argument("path")
def list_fn(forums: AllForums | DBForums, path: str) -> None:
    forum, *others = path.split("/")
    path = "/".join(others)

    html = forums.get_html(forum, path)

    panel = get_html_panel(html, title=f"{forum}/{path}")
    if panel is not None:
        print(panel)

    t = Table(title="Messages")
    t.add_column("#", style="cyan")
    t.add_column("N", style="green")
    t.add_column("Title")

    with timer("Time to read and build list"):
        for m in forums.get_msgs(forum, path):
            msgs = forums.get_msg_paths(forum, f"{path}/{m.responses.lstrip('/')}")
            entries = len(list(msgs))
            t.add_row(str(m.num), str(entries), m.title)

    print(t)


@main.command(help="Show a tree view for messages")
@convert_context
@click.argument("path")
def tree(forums: AllForums | DBForums, path: str) -> None:
    forum, *others = path.split("/")
    path = "/".join(others)

    msg: Message | URCMain = (
        forums.get_msg(forum, path) if path else forums.get_forum(forum)
    )

    tree = Tree(
        ":open_file_folder: "
        f"[link file://{forums.root}/{forum}/{path}]{forum}/{path}: {msg.title}"
    )

    with timer("Time to walk tree"):
        for _ in forums.walk_tree(forum, path, walk_tree, tree):
            pass

    print(tree)


@main.command(help="Show all parsed information for a message or main.")
@convert_context
def show(forums: AllForums | DBForums, path: str) -> None:
    forum, *others = path.split("/")
    path = "/".join(others)

    msg = forums.get_msg(forum, path) if path else forums.get_forum(forum)
    html = forums.get_html(forum, path)

    panel = get_html_panel(html, title=f"{forum}/{path}")
    if panel is not None:
        print(panel)

    print(msg)


@main.command(help="Show all forums")
@convert_context
def forums(forums: AllForums | DBForums) -> None:

    t = Table(title="Forums")
    t.add_column("#", style="cyan")
    t.add_column("Cat", style="green")
    t.add_column("Title")

    for m in track(forums.get_forums_iter(), forums.get_num_forums(), "Forums"):
        if m:
            t.add_row(str(m.num), str(m.categories), m.title)

    print(t)


@main.command(help="Populate a database with all messages")
@convert_context
def populate(db_forums: AllForums | DBForums) -> None:
    assert isinstance(db_forums, DBForums), "Must pass --db or HNDATABASE"
    con = db_forums.db
    forums = AllForums(root=db_forums.root)

    with contextlib.closing(con.cursor()) as cur:

        def log_info(msg: str) -> None:
            log_sql.info(msg, extra={"highlighter": None})

        con.set_trace_callback(log_info)

        create_forums = URCMain.sqlite_create_table_statement(
            "forums",
            {
                "num": "PRIMARY KEY",
                "responses": "UNIQUE",
                "url": "UNIQUE",
                "body": "UNIQUE",
            },
        )
        cur.execute(create_forums)

        create_members = Member.sqlite_create_table_statement(
            "people", {"user_id": "PRIMARY KEY"}
        )
        cur.execute(create_members)

        create_msgs = Message.sqlite_create_table_statement("msgs")
        cur.execute(
            create_msgs[:-3]
            + ",\n    PRIMARY KEY(forum, msg),\n    FOREIGN KEY(forum) REFERENCES forums(num)\n);"
        )

        con.set_trace_callback(None)

        insert_forum = URCMain.sqlite_insert_statement("forums")
        for forum_main in track(
            forums.get_forums_iter(),
            forums.get_num_forums(),
            "Forums",
        ):
            if forum_main:
                cur.execute(insert_forum, forum_main.as_simple_tuple())
                con.commit()

        insert_people = Member.sqlite_insert_statement("people")
        for member in track(
            forums.get_member_iter(),
            forums.get_num_members(),
            "People",
        ):
            cur.execute(insert_people, member.as_simple_tuple())

        forum_list = [f.stem for f in forums.get_forum_paths()]

        outer_progress = Progress(*PROGRESS_COLUMNS, expand=True)
        inner_progress = Progress(*PROGRESS_COLUMNS, expand=True)
        live_group = rich.console.Group(outer_progress, inner_progress)

        with rich.live.Live(live_group, refresh_per_second=10):
            insert_msg = Message.sqlite_insert_statement("msgs")
            for n, forum_each in enumerate(
                outer_progress.track(forum_list, description="Messages")
            ):
                length = forums.get_num_msgs(forum_each, "", recursive=True)

                task_id = inner_progress.add_task("Forum")
                task = inner_progress.tasks[inner_progress.task_ids.index(task_id)]

                def inner_track(
                    iterable: Iterable[T], total: int, description: str
                ) -> Iterable[T]:
                    task.description = description
                    yield from inner_progress.track(
                        iterable, total=total, task_id=task.id
                    )

                msgs = (
                    m.as_simple_tuple()
                    for m in inner_track(
                        forums.get_msgs(forum_each, "", recursive=True),
                        total=length,
                        description=f"({n}/{len(forum_list)}) {forum_each}",
                    )
                )
                cur.executemany(insert_msg, msgs)
                con.commit()
                inner_progress.remove_task(task_id)

        con.set_trace_callback(log_info)
        cur.execute("CREATE INDEX idx_msgs_up ON msgs(forum, up);")
        con.commit()
        con.set_trace_callback(None)


@main.command(help="Populate a database with full text search")
@convert_context
def populate_search(db_forums: AllForums | DBForums) -> None:
    assert isinstance(db_forums, DBForums), "Must pass --db or HNDATABASE"
    db_in = db_forums.db
    with contextlib.closing(sqlite3.connect(os.environ["HNFTSDATABASE"])) as db_out:

        db_out.execute(
            "CREATE VIRTUAL TABLE fulltext USING FTS5(forum UNINDEXED, msg UNINDEXED, date UNINDEXED, title, from_, text);"
        )

        for forum, msg, date, title, from_ in track(
            db_in.execute("SELECT forum, msg, date, title, from_ FROM msgs"),
            total=db_in.execute("SELECT COUNT(*) FROM msgs").fetchone()[0],
            description="Full text search",
        ):
            with open(
                f"../allfiles/cms-hndocs/{forum}/{msg}-body.html", encoding="Latin-1"
            ) as f:
                html_text = f.read()
            soup = BeautifulSoup(html_text, "html.parser")
            text = soup.get_text()
            db_out.execute(
                "INSERT INTO fulltext VALUES (?, ?, ?, ?, ?, ?)",
                (forum, msg, date, title, from_, text),
            )
            db_out.commit()


if __name__ == "__main__":
    _rich_traceback_guard = True
    main()  # pylint: disable=no-value-for-parameter
