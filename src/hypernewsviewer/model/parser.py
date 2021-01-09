#!/usr/bin/env python3

from __future__ import annotations

import enum
from pathlib import Path
from typing import Optional, TextIO, TypeVar

import attr
import inflection  # type: ignore

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

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

T = TypeVar("T")


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

    num_messages: Optional[int] = opt_int_field
    footer_url: Optional[str] = opt_str_field
    up_url: Optional[str] = opt_str_field
    header_url: Optional[str] = opt_str_field
    moderation: Optional[str] = opt_str_field
    user_url: Optional[str] = opt_str_field
    annotation_type: Optional[str] = opt_str_field

    @classmethod
    def from_file(cls: T, text: TextIO) -> T:
        pairs = (line.split(":", 1) for line in text)
        info = {us(k.strip()): v.strip() or None for k, v in pairs}
        return cls(**info)  # type: ignore


    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield f"[b]{self.__class__.__name__}:[/b]"
        my_table = Table("Attribute", "Value")
        for k, v in attr.asdict(self).items():
            if "url" in k and v:
                out = f"[link=URL]{v}[/link]"
            else:
                out = "" if v is None else str(v)
            my_table.add_row(k, out)
        yield my_table


@define
class URCMain(URCBase):
    list_address: str
    categories: int
    num: str

    default_outline_depth: Optional[int] = opt_int_field


@define
class URCMessage(URCBase):
    num: int = int_field

    previous_num: Optional[int] = opt_int_field
    next_num: Optional[int] = opt_int_field
    keywords: Optional[str] = opt_str_field
    up_rel: Optional[str] = opt_str_field
    node_type: Optional[str] = opt_str_field
    newsgroups: Optional[str] = opt_str_field

    message_id: str
