#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from rich.markdown import Markdown
from rich.panel import Panel
from rich.tree import Tree

from .messages import URCMessage
from .structure import get_msg_paths


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


def get_html_panel(msg: str | None, /, *, title: str) -> Panel | None:
    if msg is None:
        return None

    return Panel(
        Markdown(msg),
        title=title,
        border_style="cyan",
    )
