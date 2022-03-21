from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import attrs
import cattr
import cattr.preconf
import dateutil.parser
import inflection

from .enums import AnnotationType, ContentType

__all__ = ["converter_db", "converter_utc", "convert_url", "type_as_sqlite"]


TZOFFSETS = {
    "CET": 1 * 60 * 60,
    "CEST": 2 * 60 * 60,
}

T = TypeVar("T")


converter_utc = cattr.GenConverter()
converter_db = cattr.GenConverter()


def us(inp: str) -> str:
    retval: str = inflection.underscore(inp) if inp != "From" else "from_"
    return retval


def convert_datetime(string: str, _type: object) -> datetime:
    # Formats:
    # Mon, 05 Dec 2005 01:55:14 GMT
    # Thu Feb 14 22:20:48 CET 2008
    return dateutil.parser.parse(string, tzinfos=TZOFFSETS)


def convert_isodatetime(string: str, cls: type[datetime]) -> datetime:
    return cls.fromisoformat(string)


def convert_from_datetime(dt: datetime) -> str:
    return dt.isoformat()


converter_utc.register_structure_hook(datetime, convert_datetime)
converter_db.register_structure_hook(datetime, convert_isodatetime)
converter_db.register_unstructure_hook(datetime, convert_from_datetime)


def convert_simple(string: str, to_type: type[T]) -> T:
    return to_type(string)  # type: ignore[call-arg]


converter_utc.register_structure_hook(Path, convert_simple)
converter_db.register_structure_hook(Path, convert_simple)
converter_db.register_unstructure_hook(Path, os.fspath)


def structure_kw_attrs_fromtuple(obj: tuple[Any, ...], cls: type[T]) -> T:
    conv_obj = {}
    for a, value in zip(attrs.fields(cls), obj):
        converted = (
            converter_db._structure_attribute(  # pylint: disable=protected-access
                a, value
            )
        )
        conv_obj[a.name] = converted

    return cls(**conv_obj)


converter_db.register_structure_hook_func(
    lambda t: attrs.has(t) and any(a.kw_only for a in attrs.fields(t)),
    structure_kw_attrs_fromtuple,
)


def convert_annotation_type(string: str, t: type[AnnotationType]) -> AnnotationType:
    if string == "Message":
        return t.Message
    raise ValueError(f"Unknown annotation type {string}")


def convert_content_type(string: str, cls: type[ContentType]) -> ContentType:
    if string.startswith("Plain"):
        return cls.PlainText
    if string == "HTML":
        return cls.HTML
    if string == "Smart Text":
        return cls.SmartText
    if string == "Word Processor":
        return cls.WordProcessor
    raise ValueError(f"Unknown content type {string}")


converter_utc.register_structure_hook(ContentType, convert_content_type)
converter_utc.register_structure_hook(AnnotationType, convert_annotation_type)


def structure_from_utc(obj: str, cls: type[T]) -> T:
    pairs = (ll.split(":", 1) for line in obj.splitlines() if (ll := line.strip()))
    info = {us(k.strip()): vv for k, v in pairs if (vv := v.strip())}
    fields = attrs.fields_dict(cls)

    conv_obj = {
        name: converter_utc._structure_attribute(  # pylint: disable=protected-access
            fields[name], info[name]
        )
        for name in info
    }

    return cls(**conv_obj)


converter_utc.register_structure_hook_func(
    attrs.has,
    structure_from_utc,
)


def convert_url(string: str | None) -> str | None:
    if string is None:
        return None

    remove = "https://hypernews.cern.ch/HyperNews/CMS"
    if string.startswith(remove):
        string = string[len(remove) :]

    remove = "https://cmshypernews02.cern.ch/HyperNews/CMS"
    if string.startswith(remove):
        string = string[len(remove) :]

    if not string.endswith(".html"):
        string += ".html"

    return string


def type_as_sqlite(inp: type[Any] | None) -> str:
    if inp is None:
        return "NULL"

    try:
        suffix = "" if isinstance(None, inp) else " NOT NULL"
    except TypeError:
        # Python < 3.10 doesn't support this on Optional - but that's okay, we now know it is Optional!
        suffix = ""
        (inp,) = (t for t in inp.__args__ if not isinstance(None, t))
    assert inp is not None

    if isinstance(1, inp):
        return "INTEGER" + suffix
    if isinstance(1.0, inp):
        return "REAL" + suffix
    return "TEXT" + suffix
