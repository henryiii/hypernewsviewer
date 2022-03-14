#!/usr/bin/env python3

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple, Type, TypeVar

import attrs
import inflection

from .converter import convert_url, converter, type_as_sqlite
from .enums import AnnotationType, ContentType

Email = str
URL = str


IB = TypeVar("IB", bound="InfoBase")


def us(inp: str) -> str:
    retval: str = inflection.underscore(inp) if inp != "From" else "from_"
    return retval


@attrs.define(kw_only=True)
class InfoBase:
    @classmethod
    def from_path(cls: Type[IB], path: os.PathLike[str]) -> IB:
        with open(path, encoding="Latin-1") as f:
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

    @classmethod
    def from_simple_tuple(cls: Type[IB], info: Tuple[Any, ...]) -> IB:
        return converter.structure_attrs_fromtuple(info, cls)

    def as_simple_tuple(self) -> Tuple[Any, ...]:
        retval: Tuple[Any, ...] = converter.unstructure_attrs_astuple(self)
        return retval

    @classmethod
    def get_field_names(cls) -> List[str]:
        return [f.name for f in attrs.fields(cls)]

    @classmethod
    def get_field_types_as_sqlite(cls) -> List[str]:
        return [type_as_sqlite(f.type) for f in attrs.fields(cls)]


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
