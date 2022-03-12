#!/usr/bin/env python3

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator

from .messages import Member, URCMain, URCMessage


def get_any_urc(path: Path) -> URCMain | URCMessage:
    if path.stem.isdigit():
        return URCMessage.from_path(path.with_suffix(".html,urc"))
    else:
        return URCMain.from_path(path.with_suffix(".html,urc"))


@lru_cache(256)
def get_member(path: Path) -> Member:
    return Member.from_path(path)


@lru_cache(1)
def get_categories(path: Path) -> dict[int, str]:
    pairs = (a.split(" ", 1) for a in path.read_text().strip().splitlines())
    return {int(a): b for a, b in pairs}


@lru_cache(1)
def get_forums(directory: Path) -> list[URCMain]:
    return list(filter(None, _get_forums(directory)))


def _get_forums(directory: Path) -> Iterator[URCMain | None]:
    for path in directory.glob("*.html,urc"):
        try:
            yield URCMain.from_path(path)
        except (TypeError, ValueError) as e:
            print(f"Failed to parse: {path}:", e)
            yield None


def get_msg_paths(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.html,urc"), key=lambda x: int(x.stem))


def get_msgs(directory: Path) -> Iterator[URCMessage]:
    for path in get_msg_paths(directory):
        try:
            yield URCMessage.from_path(path)
        except ValueError as e:
            print(f"Failed to parse: {path}:", e)


def get_html(path: Path) -> str | None:
    msg = path.parent.joinpath(f"{path.stem}-body.html")
    if msg.exists():
        return msg.read_text()

    return None
