#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from rich.markdown import Markdown
from rich.panel import Panel
from rich.tree import Tree

from .parser import URCMain, URCMessage, Member


def get_any_urc(path: Path) -> URCMain | URCMessage:
    if path.stem.isdigit():
        return URCMessage.from_path(path.with_suffix(".html,urc"))
    else:
        return URCMain.from_path(path.with_suffix(".html,urc"))


def get_member(path: Path) -> Member:
    return Member.from_path(path)


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


def get_html(path: Path, /) -> str | None:
    msg = path.parent.joinpath(f"{path.stem}-body.html")
    if msg.exists():
        return msg.read_text()

    return None


def get_html_panel(path: Path, /) -> Panel | None:
    msg = get_html(path)
    if msg is None:
        return None

    return Panel(
        Markdown(msg),
        title=str(path),
        border_style="cyan",
    )
