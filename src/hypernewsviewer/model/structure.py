from __future__ import annotations

import contextlib
import logging
import sqlite3
from pathlib import Path
from typing import Callable, Generator, Iterator, TypeVar

import attrs

from .messages import Member, URCMain, URCMessage

__all__ = ["AllForums", "DBForums", "connect_forums"]

log = logging.getLogger("hypernewsviewer.sql")

T = TypeVar("T")


@attrs.define(kw_only=True)
class AllForums:
    root: Path = attrs.field(converter=Path)

    def get_msg(self, forum: str, path: str) -> URCMessage:
        assert path, "Must supply a path, use get_forum() instead for empty path"
        abspath = self.root / forum / path
        return URCMessage.from_path(abspath.with_suffix(".html,urc"))

    def get_msgs(
        self, forum: str, path: str, *, recursive: bool = False
    ) -> Iterator[URCMessage]:
        """
        This allows an empty path, unlike get_msg, since it returns the inner msgs.
        """

        for msg_path in self.get_msg_paths(forum, path):
            yield URCMessage.from_path(msg_path.with_suffix(".html,urc"))
            if recursive:
                yield from self.get_msgs(
                    forum,
                    f"{path}/{msg_path.stem}" if path else msg_path.stem,
                    recursive=True,
                )

    def get_msg_paths(self, forum: str, path: str) -> list[Path]:
        abspath = self.root / forum / path
        return sorted(abspath.glob("*?.html,urc"), key=lambda x: int(x.stem))

    def get_num_msgs(self, forum: str, path: str, *, recursive: bool = False) -> int:
        abspath = self.root / forum / path
        return len(list(abspath.glob("**/*?.html,urc" if recursive else "*?.html,urc")))

    def get_html(self, forum: str, path: str) -> str | None:
        abspath = self.root / forum / path
        msg = abspath.parent.joinpath(f"{Path(path).stem}-body.html")
        if msg.exists():
            return msg.read_text()

        return None

    def get_member(self, name: str) -> Member:
        return Member.from_path(self.root / "hnpeople" / name)

    def get_members_paths(self) -> Iterator[Path]:
        return (
            p
            for p in self.root.joinpath("hnpeople").iterdir()
            if (
                p.is_file()
                and not p.is_symlink()
                and not p.stem.startswith(".")
                and not p.suffix == ".sql3"
                and not p.name.endswith("~")
            )
        )

    def get_member_iter(self) -> Iterator[Member]:
        for path in sorted(self.get_members_paths()):
            yield Member.from_path(path)

    def get_num_members(self) -> int:
        return len(list(self.get_members_paths()))

    def get_categories(self) -> dict[int, str]:
        path = self.root / "CATEGORIES"
        pairs = (a.split(" ", 1) for a in path.read_text().strip().splitlines())
        return {int(a): b for a, b in pairs}

    def get_forum(self, forum: str) -> URCMain:
        abspath = self.root / forum
        return URCMain.from_path(abspath.with_suffix(".html,urc"))

    def get_forums_iter(self) -> Iterator[URCMain | None]:
        for path in sorted(self.root.glob("*?.html,urc")):
            try:
                yield URCMain.from_path(path)
            except (TypeError, ValueError) as e:
                print(f"Failed to parse: {path}:", e)
                yield None

    def get_forum_paths(self) -> Iterator[Path]:
        return self.root.glob("*?.html,urc")

    def get_num_forums(self) -> int:
        return len(list(self.get_forum_paths()))

    def walk_tree(
        self, forum: str, path: str, func: Callable[[Path, T], T], start: T
    ) -> Iterator[T]:
        for local_path in self.get_msg_paths(forum, path):
            branch = func(local_path, start)
            yield branch

            yield from self.walk_tree(
                forum,
                f"{path}/{local_path.stem}" if path else local_path.stem,
                func,
                branch,
            )


@attrs.define(kw_only=True)
class DBForums(AllForums):
    db: sqlite3.Connection

    def get_msg(self, forum: str, path: str) -> URCMessage:
        assert path, "Must supply a path, use get_forum() instead for empty path"
        (msg,) = self.db.execute(
            "SELECT * FROM msgs WHERE responses=?",
            (f"/{forum}/{path}",),
        )
        return URCMessage.from_simple_tuple(msg)

    def get_msgs(
        self, forum: str, path: str, *, recursive: bool = False
    ) -> Iterator[URCMessage]:
        if recursive:
            msgs = self.db.execute(
                "SELECT * FROM msgs WHERE responses LIKE ? ORDER BY responses",
                (f"/{forum}/{path}/%" if path else f"/{forum}/%",),
            )
        else:
            msgs = self.db.execute(
                "SELECT * FROM msgs WHERE up_url=?",
                (f"/get/{forum}/{path}.html" if path else f"/get/{forum}.html",),
            )
        for msg in msgs:
            yield URCMessage.from_simple_tuple(msg)

    def get_msg_paths(self, forum: str, path: str) -> list[Path]:
        responses = self.db.execute(
            "SELECT responses FROM msgs WHERE up_url=?",
            (f"/get/{forum}/{path}.html" if path else f"/get/{forum}.html",),
        )
        return sorted(
            (
                (self.root / resp[0].strip("/")).with_suffix(".html,urc")
                for resp in responses
            ),
            key=lambda x: int(x.stem),
        )

    def get_num_msgs(self, forum: str, path: str, *, recursive: bool = False) -> int:
        if recursive:
            result = self.db.execute(
                "SELECT COUNT(*) FROM msgs WHERE responses LIKE ? ORDER BY responses",
                (f"/{forum}/{path}/%" if path else f"/{forum}/%",),
            )
        else:
            result = self.db.execute(
                "SELECT COUNT(*) FROM msgs WHERE up_url=?",
                (f"/get/{forum}/{path}.html" if path else f"/get/{forum}.html",),
            )
        answer: int = result.fetchone()[0]
        return answer

    # get_html does not use the database

    def get_member(self, name: str) -> Member:
        results = list(self.db.execute("SELECT * FROM people WHERE user_id=?", (name,)))
        (member,) = results
        return Member.from_simple_tuple(member)

    def get_members_paths(self) -> Iterator[Path]:
        for (path,) in self.db.execute("SELECT user_id FROM people"):
            yield self.root / "hnpeople" / path

    def get_member_iter(self) -> Iterator[Member]:
        for member_tuple in self.db.execute("SELECT * FROM people"):
            yield Member.from_simple_tuple(member_tuple)

    # get_num_members doesn't need an optimization, it uses the database already

    # get_categories doesn't need an optimization, it reads one file only already

    def get_forum(self, forum: str) -> URCMain:
        (result,) = self.db.execute(
            "SELECT * FROM forums WHERE responses=?", (f"/{forum}",)
        )
        return URCMain.from_simple_tuple(result)

    def get_forums_iter(self) -> Iterator[URCMain]:
        for result in self.db.execute("SELECT * FROM forums"):
            yield URCMain.from_simple_tuple(result)

    def get_forum_paths(self) -> Iterator[Path]:
        for (name,) in self.db.execute("SELECT responses FROM forums"):
            yield self.root / f"{name.strip('/')}.html,urc"

    # walk_tree is only used for the CLI, so not implementing it now


@contextlib.contextmanager
def connect_forums(
    root: Path, db_path: Path | None, *, read_only: bool = False
) -> Generator[AllForums | DBForums, None, None]:
    if db_path:
        db_str = f"file:{db_path}?mode=ro" if read_only else f"file:{db_path}?mode=rwc"
        with contextlib.closing(sqlite3.connect(db_str, uri=True)) as db:
            yield DBForums(root=root, db=db)
    else:
        yield AllForums(root=root)
