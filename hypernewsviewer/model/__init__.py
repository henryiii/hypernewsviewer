#!/usr/bin/env python

from __future__ import annotations

import enum
from typing import Optional, TextIO
from pathlib import Path

import inflection  # type: ignore

import attr

import click

Date = str
Email = str
URL = str


class ContentType(enum.Enum):
    HTML = "HTML"


def us(inp: str) -> str:
    return inflection.underscore(inp) if inp != "From" else "from_"


@attr.s(kw_only=True, slots=True, auto_attribs=True, eq=True, order=False)
class URC:
    content_type: ContentType = attr.ib(converter=ContentType)
    title: str
    num_messages: int
    body: Path = attr.ib(converter=Path)
    url: URL
    categories: int
    base_url: URL
    responses: str
    date: Date
    last_message_date: Date
    last_mod: Date
    list_address: str
    num: str
    name: str
    from_: Email

    default_outline_depth: Optional[int] = attr.ib(converter=attr.converters.optional(int), default=None)
    footer_url: Optional[str] = None
    up_url: Optional[str] = None
    header_url: Optional[str] = None
    moderation: Optional[str] = None
    user_url: Optional[str] = None
    annotation_type: Optional[str] = None
    

    @classmethod
    def from_file(cls, text: TextIO) -> URC:
        pairs = (line.split(":", 1) for line in text)
        info = dict((us(k.strip()), v.strip() or None) for k, v in pairs)
        return cls(**info)  # type: ignore


@click.command()
@click.argument("input_file", type=click.File("r"))
def main(input_file: TextIO) -> None:
    urc = URC.from_file(input_file)
    print(urc)


if __name__ == "__main__":
    main()
