#!/usr/bin/env python3

from pathlib import Path
from typing import Iterator, List

from .parser import Member, URCMain, URCMessage


def get_any_urc(path: Path) -> "URCMain | URCMessage":
    if path.stem.isdigit():
        return URCMessage.from_path(path.with_suffix(".html,urc"))
    else:
        return URCMain.from_path(path.with_suffix(".html,urc"))


def get_member(path: Path) -> Member:
    return Member.from_path(path)


def get_forums(directory: Path) -> Iterator[URCMain]:
    for path in directory.glob("*.html,urc"):
        yield URCMain.from_path(path)


def get_msg_paths(directory: Path) -> List[Path]:
    return sorted(directory.glob("*.html,urc"), key=lambda x: int(x.stem))


def get_msgs(directory: Path) -> Iterator[URCMessage]:
    for path in get_msg_paths(directory):
        try:
            yield URCMessage.from_path(path)
        except ValueError as e:
            print(f"Failed to parse: {path}:", e)


def get_html(path: Path) -> "str | None":
    msg = path.parent.joinpath(f"{path.stem}-body.html")
    if msg.exists():
        return msg.read_text()

    return None
