from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO, TypeVar

import attrs
import cattr
import cattr.preconf
import inflection

__all__ = ["converter_db", "converter_utc", "convert_url", "type_as_sqlite"]


T = TypeVar("T")

# Mon, 05 Dec 2005 01:55:14 GMT
FMT = "%a, %d %b %Y %H:%M:%S %Z"
# 'Thu Feb 14 22:20:48 CET 2008'
FMT2 = "%a %b %d %H:%M:%S %Z %Y"

converter_utc = cattr.GenConverter()
converter_db = cattr.GenConverter()


def us(inp: str) -> str:
    retval: str = inflection.underscore(inp) if inp != "From" else "from_"
    return retval


def convert_datetime(string: str, _type: object = None) -> datetime:
    try:
        return datetime.strptime(string, FMT)
    except ValueError:
        return datetime.strptime(string, FMT2)


def convert_from_datetime(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S UTC")


def convert_simple(string: str, to_type: type[T]) -> T:
    return to_type(string)  # type: ignore[call-arg]


converter_utc.register_unstructure_hook(datetime, convert_from_datetime)
converter_utc.register_structure_hook(datetime, convert_datetime)

converter_db.register_unstructure_hook(datetime, convert_from_datetime)
converter_db.register_structure_hook(datetime, convert_datetime)

converter_utc.register_unstructure_hook(Path, os.fspath)
converter_utc.register_structure_hook(Path, convert_simple)

converter_db.register_unstructure_hook(Path, os.fspath)
converter_db.register_structure_hook(Path, convert_simple)


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


def structure_from_utc(obj: TextIO, cls: type[T]) -> T:
    pairs = (line.split(":", 1) for line in obj)
    info = {us(k.strip()): v.strip() or None for k, v in pairs}
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

    if not string.endswith(".html"):
        string += ".html"

    return string


def type_as_sqlite(inp: type[Any] | None) -> str:
    if inp is None:
        return "NULL"
    if isinstance(1, inp):
        return "INTEGER"
    if isinstance(1.0, inp):
        return "REAL"
    return "TEXT"
