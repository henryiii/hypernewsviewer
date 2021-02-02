#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import click
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from .parser import URCBase, URCMain, URCMessage

DIR = Path(__file__).parent.resolve()


@click.group()
@click.option(
    "--root",
    type=click.Path(exists=True, file_okay=False),
    default=DIR / "../../../../hnfiles",
)
@click.argument("path")
@click.pass_context
def main(ctx: click.Context, root: Path, path: str) -> None:
    ctx.ensure_object(dict)
    ctx.obj["root"] = root.resolve()
    ctx.obj["rootpath"] = (root.joinpath(path) if path else root).resolve()


@main.command("list")
@click.pass_context
def list_fn(ctx: click.Context) -> None:
    root: Path = ctx.obj["root"]
    rootpath: Path = ctx.obj["rootpath"]

    msg = rootpath.parent.joinpath(f"{rootpath.stem}-body.html")
    if msg.exists():
        print(
            Panel(
                Markdown(msg.read_text()),
                title=str(rootpath),
                border_style="cyan",
            )
        )

    t = Table(title="Messages")
    t.add_column("#", style="cyan")
    t.add_column("N", style="green")
    t.add_column("Title")

    for m in get_msgs(rootpath):
        msgs = get_msg_paths(root / m.responses.lstrip("/"))
        entries = len(list(msgs))
        t.add_row(str(m.num), str(entries), m.title)

    print(t)


@main.command()
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


def get_msg_paths(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.html,urc"), key=lambda x: int(x.stem))


def get_msgs(directory: Path) -> Iterator[URCMessage]:
    for path in get_msg_paths(directory):
        yield URCMessage.from_path(path)


def walk_tree(directory: Path, tree: Tree) -> None:
    for path in get_msg_paths(directory):
        folder = path.with_suffix("")
        emoji = ":open_file_folder:" if folder.exists() else ":file_folder:"
        try:
            msg_title = URCMessage.from_path(path).title
        except UnicodeDecodeError:
            ":cross_mark:"
        branch = tree.add(
            f"{emoji} [link file://{folder}]{path.stem}: {msg_title}",
        )
        if folder.exists():
            walk_tree(folder, branch)


if __name__ == "__main__":
    main(obj={})
