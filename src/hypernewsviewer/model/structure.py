#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

import click
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .parser import URCMessage

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

    msg_files = [path for path in rootpath.glob("*.html,urc")]
    urc_msgs = [URCMessage.from_path(f) for f in msg_files]
    t = Table(title="Messages")
    t.add_column("#", style="cyan")
    t.add_column("N", style="green")
    t.add_column("Title")
    for m in sorted(urc_msgs, key=lambda x: x.num):
        msgs = root.joinpath(m.responses.lstrip("/")).glob("*.html,urc")
        entries = len(list(msgs))
        t.add_row(str(m.num), str(entries), m.title)
    print(t)


if __name__ == "__main__":
    main(obj={})
