from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import attrs
import cattr
import cattr.preconf
import dateutil.parser
import dateutil.tz
import inflection

from .enums import AnnotationType, ContentType, UpRelType

__all__ = [
    "converter_utc",
    "convert_url",
    "produce_utc_dict",
]


TZOFFSETS = {
    "CET": 1 * 60 * 60,
    "CEST": 2 * 60 * 60,
}

T = TypeVar("T")


converter_utc = cattr.GenConverter()


def us(inp: str) -> str:
    return inflection.underscore(inp) if inp != "From" else "from_"


def convert_datetime(string: str, _type: object) -> datetime:
    # Formats:
    # Mon, 05 Dec 2005 01:55:14 GMT
    # Thu Feb 14 22:20:48 CET 2008
    dt = dateutil.parser.parse(string, tzinfos=TZOFFSETS)
    return dt.astimezone(dateutil.tz.UTC).replace(tzinfo=None)


def convert_isodatetime(string: str, cls: type[datetime]) -> datetime:
    return cls.fromisoformat(string)


def convert_from_datetime(dt: datetime) -> str:
    return dt.isoformat()


converter_utc.register_structure_hook(datetime, convert_datetime)


def convert_simple(string: str, to_type: type[T]) -> T:
    return to_type(string)  # type: ignore[call-arg]


converter_utc.register_structure_hook(Path, convert_simple)


def convert_annotation_type(string: str, t: type[AnnotationType]) -> AnnotationType:
    if string.lower() == "message":
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


def convert_uprel_type(string: str, cls: type[UpRelType]) -> UpRelType:
    return cls.None_ if string == "None" else cls[string]


converter_utc.register_structure_hook(ContentType, convert_content_type)
converter_utc.register_structure_hook(AnnotationType, convert_annotation_type)
converter_utc.register_structure_hook(UpRelType, convert_uprel_type)


# Raw data dict useful for testing generated properties
def produce_utc_dict(obj: str) -> dict[str, Any]:
    pairs = (ll.split(":", 1) for line in obj.splitlines() if (ll := line.strip()))
    return {us(k.strip()): vv for k, v in pairs if (vv := v.strip())}


def structure_from_utc(obj: str, cls: type[T]) -> T:
    info = produce_utc_dict(obj)
    fields = attrs.fields_dict(cls)

    conv_obj = {
        name: converter_utc._structure_attribute(  # pylint: disable=protected-access
            fields[name], info[name]
        )
        for name in (set(fields) & set(info))
    }

    for name in filter(fields, lambda x: "url" in x):
        conv_obj[name] = convert_url(conv_obj[name])

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
