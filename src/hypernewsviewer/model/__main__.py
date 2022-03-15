from __future__ import annotations

import contextlib
import os
import sqlite3
from pathlib import Path

import click
import rich.progress
import rich.traceback
from rich import print  # pylint: disable=redefined-builtin
from rich.table import Table
from rich.tree import Tree

from .cliutils import get_html_panel, walk_tree
from .messages import URCMessage
from .structure import AllForums

# pylint: disable=redefined-outer-name

rich.traceback.install(show_locals=True)

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


@click.group(help="Run with a tree path (like hnTest/1).")
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),  # type: ignore[type-var]
    default=Path(os.environ.get("HNFILES", str(DIR / "../../../../hnfiles"))),
    help="Set a different path for the data directory",
)
@click.option(
    "--db",
    default=os.environ.get("HNDATABASE", "hnvdb.sql3"),
    type=click.Path(exists=False, file_okay=False, path_type=Path),  # type: ignore[type-var]
    help="Path to the database",
)
@click.argument("path")
@click.pass_context
def main(ctx: click.Context, root: Path, path: str, db: Path) -> None:
    forum, *others = path.split("/")
    ctx.ensure_object(dict)
    ctx.obj["forums"] = AllForums(root=root)
    ctx.obj["forum"] = forum
    ctx.obj["path"] = Path("/".join(others))
    ctx.obj["db"] = db.resolve()


@main.command("list", help="Show a table of messages.")
@click.pass_context
def list_fn(ctx: click.Context) -> None:
    forums: AllForums = ctx.obj["forums"]
    forum: str = ctx.obj["forum"]
    path: Path = ctx.obj["path"]

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
def tree(ctx: click.Context) -> None:
    forums: AllForums = ctx.obj["forums"]
    forum: str = ctx.obj["forum"]
    path: Path = ctx.obj["path"]

    msg = forums.get_msg(forum, path)

    tree = Tree(
        ":open_file_folder: "
        f"[link file://{forums.root}/{forum}/{path}]{forum}/{path}: {msg.title}"
    )
    for _ in forums.walk_tree(forum, path, walk_tree, tree):
        pass
    print(tree)


@main.command(help="Show all parsed information for a message or main.")
@click.pass_context
def show(ctx: click.Context) -> None:
    forums: AllForums = ctx.obj["forums"]
    forum: str = ctx.obj["forum"]
    path: Path = ctx.obj["path"]

    msg = forums.get_msg(forum, path)
    html = forums.get_html(forum, path)

    panel = get_html_panel(html, title=f"{forum}/{path}")
    if panel is not None:
        print(panel)

    print(msg)


@main.command(help="Show all forums")
@click.pass_context
def forums(ctx: click.Context) -> None:
    forums: AllForums = ctx.obj["forums"]

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
def populate(ctx: click.Context) -> None:
    forums: AllForums = ctx.obj["forums"]
    forum: str = ctx.obj["forum"]
    path: Path = ctx.obj["path"]

    field_names = URCMessage.get_field_names()
    field_types = URCMessage.get_field_types_as_sqlite()
    columns = ", ".join(
        f"{name} {type}" for name, type in zip(field_names, field_types)
    )
    create_msg = f"CREATE TABLE msgs_{forum}({columns});"
    placeholders = ", ".join(["?"] * len(field_names))
    insert_msg = f"INSERT INTO msgs_{forum} VALUES ({placeholders});"

    length = forums.get_num_msgs(forum, path, recursive=True)

    with progress_bar() as p, contextlib.closing(
        sqlite3.connect(ctx.obj["db"])
    ) as con, contextlib.closing(con.cursor()) as cur:
        cur.execute(create_msg)
        if forum == "all":
            forum_list = forums.get_forum_names()
        else:
            forum_list = [forum]

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


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
