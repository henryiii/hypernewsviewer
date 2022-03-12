#!/usr/bin/env python3

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterator

import attrs

from .messages import Member, URCMain, URCMessage


@attrs.define(kw_only=True)
class AllForums:
    root: Path

    def get_msg(self, forum: str, path: Path | str) -> URCMain | URCMessage:
        abspath = self.root / forum / path
        if abspath.stem.isdigit():
            return URCMessage.from_path(abspath.with_suffix(".html,urc"))
        else:
            return URCMain.from_path(abspath.with_suffix(".html,urc"))

    def get_msgs(
        self, forum: str, path: Path | str
    ) -> Iterator[tuple[Path, URCMessage]]:
        for msg_path in self.get_msg_paths(forum, path):
            yield msg_path, URCMessage.from_path(msg_path.with_suffix(".html,urc"))

    def get_msg_paths(self, forum: str, path: Path | str) -> list[Path]:
        abspath = self.root / forum / path
        return sorted(abspath.glob("*.html,urc"), key=lambda x: int(x.stem))

    def get_html(self, forum: str, path: Path | str) -> str | None:
        abspath = self.root / forum / path
        msg = abspath.parent.joinpath(f"{Path(path).stem}-body.html")
        if msg.exists():
            return msg.read_text()

        return None


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
