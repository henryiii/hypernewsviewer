from __future__ import annotations

import contextlib
import os
import sqlite3
from pathlib import Path

import click
import rich.progress
import rich.traceback
from rich import print
from rich.table import Table
from rich.tree import Tree

from .cliutils import get_html_panel, walk_tree
from .parser import URCBase, URCMain, URCMessage
from .structure import _get_forums, get_msg_paths, get_msgs

rich.traceback.install(show_locals=True)

DIR = Path(__file__).parent.resolve()


def progress_bar() -> rich.progress.Progress:
    return rich.progress.Progress(
        "[green][progress.description]{task.description}",
        rich.progress.BarColumn(bar_width=None),
        "[green]{task.completed} of {task.total}",
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
    ctx.ensure_object(dict)
    ctx.obj["root"] = root.resolve()
    ctx.obj["rootpath"] = (root.joinpath(path) if path else root).resolve()
    ctx.obj["db"] = db.resolve()


@main.command("list", help="Show a table of messages.")
@click.pass_context
def list_fn(ctx: click.Context) -> None:
    root: Path = ctx.obj["root"]
    rootpath: Path = ctx.obj["rootpath"]

    panel = get_html_panel(rootpath)
    if panel is not None:
        print(panel)

    t = Table(title="Messages")
    t.add_column("#", style="cyan")
    t.add_column("N", style="green")
    t.add_column("Title")

    for m in get_msgs(rootpath):
        msgs = get_msg_paths(root / m.responses.lstrip("/"))
        entries = len(list(msgs))
        t.add_row(str(m.num), str(entries), m.title)

    print(t)


@main.command(help="Show a tree view for messages")
@click.pass_context
def tree(ctx: click.Context) -> None:
    root: Path = ctx.obj["root"]
    rootpath: Path = ctx.obj["rootpath"]

    msg: URCBase
    if rootpath.stem.isdigit():
        msg = URCMessage.from_path(rootpath.with_suffix(".html,urc"))
    else:
        msg = URCMain.from_path(rootpath.with_suffix(".html,urc"))
    tree = Tree(
        ":open_file_folder: "
        f"[link file://{rootpath}]{rootpath.relative_to(root)}: {msg.title}"
    )
    walk_tree(rootpath, tree)
    print(tree)


@main.command(help="Show all parsed information for a message or main.")
@click.pass_context
def show(ctx: click.Context) -> None:
    rootpath: Path = ctx.obj["rootpath"]

    panel = get_html_panel(rootpath)
    if panel is not None:
        print(panel)

    URC: type[URCBase] = URCMessage if rootpath.stem.isdigit() else URCMain
    urc = URC.from_path(rootpath.with_suffix(".html,urc"))
    print(urc)


@main.command(help="Show all forums")
@click.pass_context
def forums(ctx: click.Context) -> None:
    root: Path = ctx.obj["root"]

    t = Table(title="Forums")
    t.add_column("#", style="cyan")
    t.add_column("Cat", style="green")
    t.add_column("Title")

    length = len(list(root.glob("*.html,urc")))
    with progress_bar() as p:
        for m in p.track(_get_forums(root), total=length):
            if m:
                t.add_row(str(m.num), str(m.categories), m.title)

    print(t)


@main.command(help="Populate a database with all messages")
@click.pass_context
def populate(ctx: click.Context) -> None:
    rootpath: Path = ctx.obj["rootpath"]

    field_names = URCMessage.get_field_names()
    field_types = URCMessage.get_field_types_as_sqlite()
    columns = ", ".join(
        f"{name} {type}" for name, type in zip(field_names, field_types)
    )
    create_msg = f"CREATE TABLE msgs_{rootpath.stem}(path STRING, {columns});"
    placeholders = ", ".join(["?"] * (len(field_names) + 1))
    insert_msg = f"INSERT INTO msgs_{rootpath.stem} VALUES ({placeholders});"

    length = len(list(rootpath.glob("*.html,urc")))

    with progress_bar() as p, contextlib.closing(
        sqlite3.connect(ctx.obj["db"])
    ) as con, contextlib.closing(con.cursor()) as cur:

        cur.execute(create_msg)
        for m in p.track(get_msgs(rootpath), total=length):
            if m:
                values = m.as_simple_tuple()
                with con:
                    cur.execute(insert_msg, values)


if __name__ == "__main__":
    main()
