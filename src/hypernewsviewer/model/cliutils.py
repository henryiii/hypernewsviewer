#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from rich.markdown import Markdown
from rich.panel import Panel
from rich.tree import Tree

from .messages import URCMessage


def walk_tree(path: Path, tree: Tree) -> Tree:
    folder = path.with_suffix("")
    emoji = (
        ":open_file_folder:"
        if folder.joinpath("responses.html").exists()
        else ":file_folder:"
    )
    try:
        msg_title = URCMessage.from_path(path).title
    except UnicodeDecodeError:
        msg_title = ":cross_mark:"
    return tree.add(
        f"{emoji} [link file://{folder}]{path.stem}: {msg_title}",
    )


def get_html_panel(msg: str | None, /, *, title: str) -> Panel | None:
    if msg is None:
        return None

    return Panel(
        Markdown(msg),
        title=title,
        border_style="cyan",
    )
