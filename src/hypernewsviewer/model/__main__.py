# pylint: disable=cell-var-from-loop
from __future__ import annotations

import contextlib
import functools
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Callable, Generator, Iterable, TypeVar

import click
import rich.console
import rich.live
import rich.progress
import rich.traceback
import sqlalchemy
from bs4 import BeautifulSoup
from rich import print
from rich.progress import Progress, Task
from rich.table import Table
from rich.tree import Tree
from sqlalchemy import select
from sqlalchemy.orm import Session

from .._compat.typing import Concatenate, ParamSpec
from .cliutils import get_html_panel, walk_tree
from .messages import URCMain, URCMessage
from .orm import mapper_registry
from .structure import AllForums, DBForums, connect_forums

# pylint: disable=redefined-outer-name

rich.traceback.install(suppress=[click, rich, sqlalchemy], show_locals=True, width=None)

T = TypeVar("T")
P = ParamSpec("P")

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
    function: Callable[Concatenate[AllForums | DBForums, P], None]
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

    msg: URCMessage | URCMain = (
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
@click.argument("path")
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
    engine = db_forums.engine
    forums = AllForums(root=db_forums.root)

    engine.echo = True

    with Session(engine) as session:
        mapper_registry.metadata.create_all(engine)

    engine.echo = False

    with Session(engine) as session:
        for forum_main in track(
            forums.get_forums_iter(),
            forums.get_num_forums(),
            "Forums",
        ):
            if forum_main:
                session.add(forum_main)

        session.commit()

        for member in track(
            forums.get_member_iter(),
            forums.get_num_members(),
            "People",
        ):
            session.add(member)

        session.commit()

        forum_list = [f.stem for f in forums.get_forum_paths()]

        outer_progress = Progress(*PROGRESS_COLUMNS, expand=True)
        inner_progress = Progress(*PROGRESS_COLUMNS, expand=True)
        live_group = rich.console.Group(outer_progress, inner_progress)

        with rich.live.Live(live_group, refresh_per_second=10):
            for n, forum_each in enumerate(
                outer_progress.track(forum_list, description="Messages")
            ):
                length = forums.get_num_msgs(forum_each, "", recursive=True)

                task_id = inner_progress.add_task("Forum")
                task = inner_progress.tasks[inner_progress.task_ids.index(task_id)]

                def inner_track(
                    iterable: Iterable[T], total: int, description: str, task: Task
                ) -> Iterable[T]:
                    task.description = description
                    yield from inner_progress.track(
                        iterable, total=total, task_id=task.id
                    )

                for msg in inner_track(
                    forums.get_msgs(forum_each, "", recursive=True),
                    total=length,
                    description=f"({n}/{len(forum_list)}) {forum_each}",
                    task=task,
                ):
                    session.add(msg)

                session.commit()

                inner_progress.remove_task(task_id)


@main.command(help="Populate a database with full text search")
@convert_context
@click.option(
    "--fts",
    default=Path(os.environ["HNFTSDATABASE"])
    if "HNFTSDATABASE" in os.environ
    else None,
    type=click.Path(file_okay=True, exists=False, path_type=Path),  # type: ignore[type-var]
    help="Path to make the fts database",
)
def populate_search(db_forums: AllForums | DBForums, fts: Path) -> None:
    assert isinstance(db_forums, DBForums), "Must pass --db or HNDATABASE"
    with contextlib.closing(sqlite3.connect(str(fts))) as db_out, Session(
        db_forums.engine
    ) as session:
        db_out.execute(
            "CREATE VIRTUAL TABLE fulltext USING FTS5(responses UNINDEXED, date UNINDEXED, title, from_, text);"
        )

        total = session.execute(
            select(sqlalchemy.func.count(URCMessage.responses))
        ).scalar_one()
        selection = select(
            URCMessage.responses, URCMessage.date, URCMessage.title, URCMessage.from_
        )
        result = session.execute(selection)
        for responses, date, title, from_ in track(
            result,
            total=int(total),
            description="Full text search",
        ):
            html_text = Path(f"{db_forums.root}{responses}-body.html").read_text(
                encoding="Latin-1"
            )
            soup = BeautifulSoup(html_text, "html.parser")
            text = soup.get_text()
            db_out.execute(
                "INSERT INTO fulltext VALUES (?, ?, ?, ?, ?)",
                (responses, date, title, from_, text),
            )
        db_out.commit()

        db_out.set_trace_callback(log_sql.info)
        db_out.execute("CREATE INDEX date_index ON fulltext_content(c1);")
        db_out.execute("INSERT INTO fulltext(fulltext) VALUES('optimize');")
        db_out.commit()


if __name__ == "__main__":
    _rich_traceback_guard = True
    main()  # pylint: disable=no-value-for-parameter
