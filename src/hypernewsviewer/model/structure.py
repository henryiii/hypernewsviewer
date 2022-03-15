#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator, TypeVar

import attrs

from .messages import Member, URCMain, URCMessage

T = TypeVar("T")


@attrs.define(kw_only=True)
class AllForums:
    root: Path

    def get_msg(self, forum: str, path: Path | str) -> URCMain | URCMessage:
        abspath = self.root / forum / path
        if abspath.stem.isdigit():
            return URCMessage.from_path(abspath.with_suffix(".html,urc"))

        return URCMain.from_path(abspath.with_suffix(".html,urc"))

    def get_msgs(
        self, forum: str, path: Path | str, *, recursive: bool = False
    ) -> Iterator[URCMessage]:
        for msg_path in self.get_msg_paths(forum, path):
            yield URCMessage.from_path(msg_path.with_suffix(".html,urc"))
            if recursive:
                yield from self.get_msgs(
                    forum, Path(path) / msg_path.stem, recursive=True
                )

    def get_msg_paths(self, forum: str, path: Path | str) -> list[Path]:
        abspath = self.root / forum / path
        return sorted(abspath.glob("*.html,urc"), key=lambda x: int(x.stem))

    def get_num_msgs(
        self, forum: str, path: Path | str, *, recursive: bool = False
    ) -> int:
        abspath = self.root / forum / path
        return len(list(abspath.glob("**/*.html,urc" if recursive else "*.html,urc")))

    def get_html(self, forum: str, path: Path | str) -> str | None:
        abspath = self.root / forum / path
        msg = abspath.parent.joinpath(f"{Path(path).stem}-body.html")
        if msg.exists():
            return msg.read_text()

        return None

    def get_member(self, name: str) -> Member:
        return Member.from_path(self.root / "hnpeople" / name)

    def get_categories(self) -> dict[int, str]:
        path = self.root / "CATEGORIES"
        pairs = (a.split(" ", 1) for a in path.read_text().strip().splitlines())
        return {int(a): b for a, b in pairs}

    def get_num_forums(self) -> int:
        return len(list(self.root.glob("*.html,urc")))

    def get_forum_names(self) -> list[str]:
        return [f.stem for f in self.root.glob("*.html,urc")]

    def get_forums_iter(self) -> Iterator[URCMain | None]:
        for path in self.root.glob("*.html,urc"):
            try:
                yield URCMain.from_path(path)
            except (TypeError, ValueError) as e:
                print(f"Failed to parse: {path}:", e)
                yield None

    def walk_tree(
        self, forum: str, path: Path | str, func: Callable[[Path, T], T], start: T
    ) -> Iterator[T]:
        for local_path in self.get_msg_paths(forum, path):
            branch = func(local_path, start)
            yield branch

            yield from self.walk_tree(forum, Path(path) / local_path.stem, func, branch)
