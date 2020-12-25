#!/usr/bin/env python3

from __future__ import annotations

import enum
from pathlib import Path
from typing import List, Optional, TextIO, TypeVar

import attr

import click

import inflection  # type: ignore


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


@attr.define()
class URCBase:
    content_type: ContentType = attr.field(converter=ContentType)
    title: str
    body: Path = attr.ib(converter=Path)
    url: URL
    base_url: URL
    responses: str
    date: Date
    last_message_date: Date
    last_mod: Date
    num: int = int_field
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
        info = dict((us(k.strip()), v.strip() or None) for k, v in pairs)
        return cls(**info)  # type: ignore


@define
class URCMain(URCBase):
    list_address: str
    categories: int

    default_outline_depth: Optional[int] = opt_int_field


@define
class URCMessage(URCBase):
    previous_num: Optional[int] = opt_int_field
    next_num: Optional[int] = opt_int_field
    keywords: Optional[str] = opt_str_field
    up_rel: Optional[str] = opt_str_field
    node_type: Optional[str] = opt_str_field
    newsgroups: Optional[str] = opt_str_field

    message_id: str


@click.command()
@click.argument("input_file", type=click.File("r", lazy=True), nargs=-1)
@click.option("--kind", type=click.Choice(Kind), required=True)
def main(input_file: List[TextIO], kind: Kind) -> None:
    URC = URCMain if kind == Kind.main else URCMessage
    for ifile in input_file:
        with ifile as file:
            urc = URC.from_file(file)
            print(urc)


if __name__ == "__main__":
    main()
