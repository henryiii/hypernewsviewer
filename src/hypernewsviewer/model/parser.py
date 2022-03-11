#!/usr/bin/env python3

import enum
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TextIO, Type, TypeVar

import attrs
import cattr
import inflection

Email = str
URL = str


class ContentType(str, enum.Enum):
    HTML = "HTML"
    SmartText = "Smart Text"
    PlainText = "Plain Text"
    WordProcessor = "Word Processor"


class Kind(str, enum.Enum):
    main = "main"
    msg = "msg"


class AnnotationType(str, enum.Enum):
    Message = "Message"


def us(inp: str) -> str:
    retval: str = inflection.underscore(inp) if inp != "From" else "from_"
    return retval


T = TypeVar("T")
IB = TypeVar("IB", bound="InfoBase")

# Mon, 05 Dec 2005 01:55:14 GMT
FMT = "%a, %d %b %Y %H:%M:%S %Z"
# 'Thu Feb 14 22:20:48 CET 2008'
FMT2 = "%a %b %d %H:%M:%S %Z %Y"

converter = cattr.GenConverter()


def convert_datetime(string: str, _type: object = None) -> datetime:
    try:
        return datetime.strptime(string, FMT)
    except ValueError:
        return datetime.strptime(string, FMT2)


def convert_from_datetime(dt: datetime) -> str:
    return dt.strftime(FMT)


converter.register_unstructure_hook(datetime, convert_from_datetime)
converter.register_structure_hook(datetime, convert_datetime)


def convert_simple(string: str, type: Type[T]) -> T:
    return type(string)  # type: ignore[call-arg]


converter.register_unstructure_hook(Path, str)
converter.register_structure_hook(Path, convert_simple)


def convert_url(string: Optional[str]) -> Optional[str]:
    remove = "https://hypernews.cern.ch/HyperNews/CMS"
    if string and string.startswith(remove):
        string = string[len(remove) :]

    return string


@attrs.define(kw_only=True)
class InfoBase:
    @classmethod
    def from_path(cls: Type[IB], path: os.PathLike[str]) -> IB:
        with open(path) as f:
            return cls.from_file(f)

    @classmethod
    def from_file(cls: Type[IB], text: TextIO) -> IB:
        pairs = (line.split(":", 1) for line in text)
        info = {us(k.strip()): v.strip() or None for k, v in pairs}
        return cls.from_dict(info)

    @classmethod
    def from_dict(cls: Type[IB], info: Dict[str, Any]) -> IB:
        return converter.structure(info, cls)

    def as_simple_dict(self) -> Dict[str, Any]:
        retval: Dict[str, Any] = converter.unstructure(self)
        return retval


@attrs.define(kw_only=True)
class Member(InfoBase):
    session_length: str
    status: str
    user_id: str
    format: str
    hide: str
    password: str
    user_url: str
    content: str
    email: str
    name: str
    email2: Optional[str] = None
    subscribe: Optional[str] = None
    alt_user_i_ds: Optional[str] = None


@attrs.define(kw_only=True)
class URCBase(InfoBase):
    content_type: ContentType
    title: str
    body: Path
    url: URL = attrs.field(converter=convert_url)
    base_url: URL = attrs.field(converter=convert_url)
    responses: str
    date: datetime
    last_message_date: datetime
    last_mod: datetime
    name: str
    from_: Email

    num_messages: Optional[int] = None
    footer_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    up_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    header_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    moderation: Optional[str] = None
    user_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    annotation_type: Optional[AnnotationType] = None


@attrs.define(kw_only=True)
class URCMain(URCBase):
    list_address: str
    categories: int
    num: str

    default_outline_depth: Optional[int] = None


@attrs.define(kw_only=True)
class URCMessage(URCBase):
    num: int

    previous_num: Optional[int] = None
    next_num: Optional[int] = None
    keywords: Optional[str] = None
    up_rel: Optional[str] = None
    node_type: Optional[str] = None
    newsgroups: Optional[URL] = attrs.field(converter=convert_url, default=None)

    message_id: str
