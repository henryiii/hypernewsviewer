from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any, Callable, Generator, Iterator, TypeVar

import attrs
import sqlalchemy
from sqlalchemy import select
from sqlalchemy.orm import Session

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
        if path:
            abspath = self.root / forum / path
            msg = abspath.parent.joinpath(f"{Path(path).stem}-body.html")
        else:
            msg = self.root.joinpath(f"{forum}.note")
        if msg.exists():
            return msg.read_text()

        return None

    def get_member(self, user_id: str) -> Member:
        return Member.from_path(self.root / "hnpeople" / user_id)

    def get_members_paths(self) -> Iterator[Path]:
        return (
            p
            for p in self.root.joinpath("hnpeople").iterdir()
            if p.is_file()
            and not p.is_symlink()
            and not p.stem.startswith(".")
            and p.suffix != ".sql3"
            and not p.name.endswith("~")
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
                print(f"Failed to parse: {path}:", e)  # noqa: T201
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
    engine: Any

    def get_msg(self, forum: str, path: str) -> URCMessage:
        assert path, "Must supply a path, use get_forum() instead for empty path"
        selection = select(URCMessage).where(URCMessage.responses == f"/{forum}/{path}")
        with Session(self.engine) as session:
            msg: URCMessage | None = session.execute(selection).scalar_one_or_none()
        if msg is None:
            errmsg = f"No such message: /{forum}/{path}"
            raise FileNotFoundError(errmsg)
        return msg

    @staticmethod
    def _get_msg_listing(forum: str, path: str, recursive: bool) -> Any:
        if recursive:
            return URCMessage.responses.like(  # type: ignore[attr-defined]
                f"/{forum}/" + (f"{path}/%" if path else "%")
            )
        return URCMessage.up_url == (
            f"/get/{forum}/{path}.html" if path else f"/get/{forum}.html"
        )

    def get_msgs(
        self, forum: str, path: str, *, recursive: bool = False
    ) -> Iterator[URCMessage]:
        selection = select(URCMessage).where(
            self._get_msg_listing(forum, path, recursive)
        )
        if recursive:
            selection = selection.order_by(URCMessage.responses)

        with Session(self.engine) as session:
            yield from session.execute(selection).scalars()

    def get_msg_paths(self, forum: str, path: str) -> list[Path]:
        selection = select(URCMessage.responses).where(
            self._get_msg_listing(forum, path, recursive=False)
        )

        with Session(self.engine) as session:
            return sorted(
                (
                    (self.root / resp.strip("/")).with_suffix(".html,urc")
                    for resp in session.execute(selection).scalars()
                ),
                key=lambda x: int(x.stem),
            )

    def get_num_msgs(self, forum: str, path: str, *, recursive: bool = False) -> int:
        selection = select(sqlalchemy.func.count(URCMessage.responses)).where(
            self._get_msg_listing(forum, path, recursive)
        )
        with Session(self.engine) as session:
            return session.execute(selection).scalar()  # type: ignore[no-any-return]

    # get_html does not use the database

    def get_member(self, user_id: str) -> Member:
        selection = select(Member).where(Member.user_id == user_id)
        with Session(self.engine) as session:
            return session.execute(selection).scalar_one()  # type: ignore[no-any-return]

    def get_members_paths(self) -> Iterator[Path]:
        selection = select(Member.user_id)
        with Session(self.engine) as session:
            for path in session.execute(selection).scalars():
                yield self.root / "hnpeople" / path

    def get_member_iter(self) -> Iterator[Member]:
        selection = select(Member)
        with Session(self.engine) as session:
            yield from session.execute(selection).scalars()

    # get_num_members doesn't need an optimization, it uses the database already

    # get_categories doesn't need an optimization, it reads one file only already

    def get_forum(self, forum: str) -> URCMain:
        selection = select(URCMain).where(URCMain.responses == f"/{forum}")
        with Session(self.engine) as session:
            return session.execute(selection).scalar_one()  # type: ignore[no-any-return]

    def get_forums_iter(self) -> Iterator[URCMain]:
        selection = select(URCMain)
        with Session(self.engine) as session:
            yield from session.execute(selection).scalars()

    def get_forum_paths(self) -> Iterator[Path]:
        selection = select(URCMain.responses)
        with Session(self.engine) as session:
            for name in session.execute(selection).scalars():
                yield self.root / f"{name.strip('/')}.html,urc"

    # walk_tree is only used for the CLI, so not implementing it now


@contextlib.contextmanager
def connect_forums(
    root: Path, db_path: Path | None
) -> Generator[AllForums | DBForums, None, None]:
    if db_path:
        db_str = f"sqlite:///{db_path}"
        engine = sqlalchemy.create_engine(db_str, future=True)
        yield DBForums(root=root, engine=engine)
    else:
        yield AllForums(root=root)
