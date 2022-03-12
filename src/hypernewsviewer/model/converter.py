from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

import cattr

__all__ = ["converter", "convert_url", "type_as_sqlite"]


T = TypeVar("T")

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


def type_as_sqlite(inp: Optional[Type[Any]]) -> str:
    if inp is None:
        return "NULL"
    if isinstance(1, inp):
        return "INTEGER"
    if isinstance(1.0, inp):
        return "REAL"
    return "TEXT"
