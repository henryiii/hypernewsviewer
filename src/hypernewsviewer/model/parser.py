#!/usr/bin/env python3

from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import Any, TextIO, TypeVar

import attr
import inflection
from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

Date = str
Email = str
URL = str


class ContentType(enum.Enum):
    HTML = "HTML"
    SmartText = "Smart Text"
    PlainText = "Plain Text"


class Kind(str, enum.Enum):
    main = "main"
    msg = "msg"


def us(inp: str) -> str:
    retval: str = inflection.underscore(inp) if inp != "From" else "from_"
    return retval


# not using provisional API like attr.define due to missing type info for it
define = attr.s(
    kw_only=True,
    slots=True,
    auto_attribs=True,
    eq=True,
    order=False,
)

int_field = attr.ib(converter=int)
opt_int_field = attr.ib(converter=attr.converters.optional(int), default=None)
opt_str_field = attr.ib(converter=attr.converters.optional(str), default=None)

T = TypeVar("T", bound="URCBase")


@define
class URCBase:
    content_type: ContentType = attr.ib(converter=ContentType)
    title: str
    body: Path = attr.ib(converter=Path)
    url: URL
    base_url: URL
    responses: str
    date: Date
    last_message_date: Date
    last_mod: Date
    name: str
    from_: Email

    num_messages: int | None = opt_int_field
    footer_url: str | None = opt_str_field
    up_url: str | None = opt_str_field
    header_url: str | None = opt_str_field
    moderation: str | None = opt_str_field
    user_url: str | None = opt_str_field
    annotation_type: str | None = opt_str_field

    @classmethod
    def from_path(cls: type[T], path: os.PathLike[str]) -> T:
        with open(path) as f:
            return cls.from_file(f)

    @classmethod
    def from_file(cls: type[T], text: TextIO) -> T:
        pairs = (line.split(":", 1) for line in text)
        info = {us(k.strip()): v.strip() or None for k, v in pairs}
        return cls(**info)  # type: ignore

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield f"[b]{self.__class__.__name__}:[/b]"
        my_table = Table("Attribute", "Value")
        for k, v in attr.asdict(self).items():
            if "url" in k and v:
                out = f"[link=URL]{v}[/link]"
            else:
                out = "" if v is None else str(v)
            my_table.add_row(k, out)
        yield my_table

    def as_simple_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in attr.asdict(self).items()}


@define
class URCMain(URCBase):
    list_address: str
    categories: int
    num: str

    default_outline_depth: int | None = opt_int_field


@define
class URCMessage(URCBase):
    num: int = int_field

    previous_num: int | None = opt_int_field
    next_num: int | None = opt_int_field
    keywords: str | None = opt_str_field
    up_rel: str | None = opt_str_field
    node_type: str | None = opt_str_field
    newsgroups: str | None = opt_str_field

    message_id: str
