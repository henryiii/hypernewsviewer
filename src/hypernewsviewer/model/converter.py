from __future__ import annotations

from datetime import datetime
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
    "produce_utc_dict",
]


TZOFFSETS = {
    "CET": 1 * 60 * 60,
    "CEST": 2 * 60 * 60,
}


def us(inp: str) -> str:
    return inflection.underscore(inp) if inp != "From" else "from_"  # type: ignore[no-any-return]


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


def convert_datetime(string: str, _type: object) -> datetime:
    # Formats:
    # Mon, 05 Dec 2005 01:55:14 GMT
    # Thu Feb 14 22:20:48 CET 2008
    dt = dateutil.parser.parse(string, tzinfos=TZOFFSETS)
    return dt.astimezone(dateutil.tz.UTC).replace(tzinfo=None)


def convert_annotation_type(string: str, t: type[AnnotationType]) -> AnnotationType:
    if string.lower() == "message":
        return t.Message
    msg = f"Unknown annotation type {string}"
    raise ValueError(msg)


def convert_content_type(string: str, cls: type[ContentType]) -> ContentType:
    if string.startswith("Plain"):
        return cls.PlainText
    if string == "HTML":
        return cls.HTML
    if string == "Smart Text":
        return cls.SmartText
    if string == "Word Processor":
        return cls.WordProcessor
    msg = f"Unknown content type {string}"
    raise ValueError(msg)


def convert_uprel_type(string: str, cls: type[UpRelType]) -> UpRelType:
    return cls.None_ if string == "None" else cls[string]


converter_utc = cattr.GenConverter()
converter_utc.register_structure_hook(datetime, convert_datetime)
converter_utc.register_structure_hook(ContentType, convert_content_type)
converter_utc.register_structure_hook(AnnotationType, convert_annotation_type)
converter_utc.register_structure_hook(UpRelType, convert_uprel_type)


# Raw data dict useful for testing generated properties
def produce_utc_dict(obj: str) -> dict[str, Any]:
    pairs = (ll.split(":", 1) for line in obj.splitlines() if (ll := line.strip()))
    return {us(k.strip()): vv for k, v in pairs if (vv := v.strip())}


T = TypeVar("T", bound=attrs.AttrsInstance)


def structure_from_utc(obj: str, cls: type[T]) -> T:
    info = produce_utc_dict(obj)
    fields = attrs.fields_dict(cls)

    conv_obj = {
        name: converter_utc._structure_attribute(  # pylint: disable=protected-access
            fields[name], info[name]
        )
        for name in (set(fields) & set(info))
    }

    for name in (x for x in conv_obj if "url" in x):
        conv_obj[name] = convert_url(conv_obj[name])

    return cls(**conv_obj)


converter_utc.register_structure_hook_func(
    attrs.has,
    structure_from_utc,
)
