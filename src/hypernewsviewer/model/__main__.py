from __future__ import annotations

import contextlib
import functools
import os
import sqlite3
from pathlib import Path
from typing import Callable, Generator

import click
import rich.progress
import rich.traceback
from rich import print  # pylint: disable=redefined-builtin
from rich.table import Table
from rich.tree import Tree

from .cliutils import get_html_panel, walk_tree
from .messages import Member, URCMain, URCMessage
from .structure import AllForums, DBForums

# pylint: disable=redefined-outer-name

rich.traceback.install(suppress=[click, rich], show_locals=True)

DIR = Path(__file__).parent.resolve()


def progress_bar() -> rich.progress.Progress:
    return rich.progress.Progress(
        "[green][progress.description]{task.description}",
        rich.progress.BarColumn(bar_width=None),
        "[green]{task.completed} of {task.total:g}",
        "[progress.percentage]{task.percentage:>3.0f}%",
        rich.progress.TimeElapsedColumn(),
        rich.progress.TimeRemainingColumn(),
        expand=True,
    )


@contextlib.contextmanager
def connect_db(
    root: Path, db_path: Path | None
) -> Generator[AllForums | DBForums, None, None]:
    if db_path:
        with contextlib.closing(sqlite3.connect(str(db_path))) as db:
            yield DBForums(root=root, db=db)
    else:
        yield AllForums(root=root)


def convert_context(
    function: Callable[[str, Path, AllForums | DBForums], None]
) -> Callable[[click.Context], None]:
    """
    Decorator to convert the context to a DBForums or AllForums object.
    """

    @functools.wraps(function)
    def wrapper(ctx: click.Context) -> None:
        forum: str = ctx.obj["forum"]
        path: Path = ctx.obj["path"]

        with connect_db(ctx.obj["root"], ctx.obj["db"]) as forums:
            function(forum, path, forums)

    return wrapper


@click.group(help="Run with a tree path (like hnTest/1).")
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
@click.argument("path")
@click.pass_context
def main(ctx: click.Context, root: Path, db: Path | None, path: str) -> None:
    forum, *others = path.split("/")
    ctx.ensure_object(dict)
    ctx.obj["forum"] = forum
    ctx.obj["path"] = Path("/".join(others))
    ctx.obj["db"] = db.resolve() if db else None
    ctx.obj["root"] = root.resolve()


@main.command("list", help="Show a table of messages.")
@click.pass_context
def list_fn(ctx: click.Context) -> None:
    forum: str = ctx.obj["forum"]
    path: Path = ctx.obj["path"]

    with connect_db(ctx.obj["root"], ctx.obj["db"]) as forums:
        html = forums.get_html(forum, path)

        panel = get_html_panel(html, title=f"{forum}/{path}")
        if panel is not None:
            print(panel)

        t = Table(title="Messages")
        t.add_column("#", style="cyan")
        t.add_column("N", style="green")
        t.add_column("Title")

        for m in forums.get_msgs(forum, path):
            msgs = forums.get_msg_paths(forum, path / m.responses.lstrip("/"))
            entries = len(list(msgs))
            t.add_row(str(m.num), str(entries), m.title)

        print(t)


@main.command(help="Show a tree view for messages")
@click.pass_context
@convert_context
def tree(forum: str, path: Path, forums: AllForums | DBForums) -> None:
    msg = forums.get_forum(forum) if path == Path() else forums.get_msg(forum, path)

    tree = Tree(
        ":open_file_folder: "
        f"[link file://{forums.root}/{forum}/{path}]{forum}/{path}: {msg.title}"
    )
    for _ in forums.walk_tree(forum, path, walk_tree, tree):
        pass

    print(tree)


@main.command(help="Show all parsed information for a message or main.")
@click.pass_context
@convert_context
def show(forum: str, path: Path, forums: AllForums | DBForums) -> None:
    msg = forums.get_forum(forum) if path == Path() else forums.get_msg(forum, path)
    html = forums.get_html(forum, path)

    panel = get_html_panel(html, title=f"{forum}/{path}")
    if panel is not None:
        print(panel)

    print(msg)


@main.command(help="Show all forums")
@click.pass_context
@convert_context
def forums(_forum: str, _path: Path, forums: AllForums | DBForums) -> None:

    t = Table(title="Forums")
    t.add_column("#", style="cyan")
    t.add_column("Cat", style="green")
    t.add_column("Title")

    with progress_bar() as p:
        for m in p.track(forums.get_forums_iter(), total=forums.get_num_forums()):
            if m:
                t.add_row(str(m.num), str(m.categories), m.title)

    print(t)


@main.command(help="Populate a database with all messages")
@click.pass_context
@convert_context
def populate(forum: str, path: Path, db_forums: AllForums | DBForums) -> None:
    assert isinstance(db_forums, DBForums), "Must pass --db or HNDATABASE"
    con = db_forums.db
    forums = AllForums(root=db_forums.root)

    length = forums.get_num_msgs(forum, path, recursive=True)
    contraint_msgs = {"responses": "PRIMARY KEY", "url": "UNIQUE", "body": "UNIQUE"}
    contraint_forums = {
        "num": "PRIMARY KEY",
        "responses": "UNIQUE",
        "url": "UNIQUE",
        "body": "UNIQUE",
    }

    with progress_bar() as p, contextlib.closing(con.cursor()) as cur:
        cur.execute(
            URCMessage.sqlite_create_table_statement("msgs", contraint_msgs) + ";"
        )
        forum_list = (
            [f.stem for f in forums.get_forum_paths()]
            if forum == "all"
            else forum.split()
        )

        insert_msg = URCMessage.sqlite_insert_statement("msgs")
        for forum_each in forum_list:
            length = forums.get_num_msgs(forum_each, path, recursive=True)
            msgs = (
                m.as_simple_tuple()
                for m in p.track(
                    forums.get_msgs(forum_each, path, recursive=True),
                    total=length,
                    description=forum_each,
                )
                if m
            )
            cur.executemany(insert_msg, msgs)

        cur.execute(
            URCMain.sqlite_create_table_statement("forums", contraint_forums)
            + " WITHOUT ROWID;"
        )
        insert_forum = URCMain.sqlite_insert_statement("forums")
        for forum_main in p.track(
            forums.get_forums_iter(),
            total=forums.get_num_forums(),
            description="Forums",
        ):
            if forum_main:
                cur.execute(insert_forum, forum_main.as_simple_tuple())

        cur.execute(
            Member.sqlite_create_table_statement("people", {"user_id": "PRIMARY KEY"})
            + " WITHOUT ROWID;"
        )
        insert_people = Member.sqlite_insert_statement("people")
        for member in p.track(
            forums.get_member_iter(),
            total=forums.get_num_members(),
            description="People",
        ):
            if member:
                cur.execute(insert_people, member.as_simple_tuple())

        con.commit()


if __name__ == "__main__":
    _rich_traceback_guard = True
    main()  # pylint: disable=no-value-for-parameter
