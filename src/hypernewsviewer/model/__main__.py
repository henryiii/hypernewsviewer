from __future__ import annotations

from pathlib import Path

import click
import rich.traceback
from rich import print
from rich.table import Table
from rich.tree import Tree

from .parser import URCBase, URCMain, URCMessage
from .structure import get_msg_paths, get_msgs
from .cliutils imoport get_html_panel, walk_tree

rich.traceback.install(show_locals=True)

DIR = Path(__file__).parent.resolve()


@click.group(help="Run with a tree path (like hnTest/1).")
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False),
    default=DIR / "../../../../hnfiles",
    help="Set a different path for the data directory",
)
@click.argument("path")
@click.pass_context
def main(ctx: click.Context, root: Path, path: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["root"] = root.resolve()
    ctx.obj["rootpath"] = (root.joinpath(path) if path else root).resolve()


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

    URC = URCMessage if rootpath.stem.isdigit() else URCMain
    urc = URC.from_path(rootpath.with_suffix(".html,urc"))
    print(urc)


if __name__ == "__main__":
    main()
