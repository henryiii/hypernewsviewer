import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import attrs

from .converter import convert_url, converter_db, converter_utc, type_as_sqlite
from .enums import AnnotationType, ContentType

Email = str
URL = str

IB = TypeVar("IB", bound="InfoBase")


@attrs.define(kw_only=True, eq=True, frozen=True)
class InfoBase:
    @classmethod
    def from_path(cls: Type[IB], path: os.PathLike[str]) -> IB:
        with open(path, "rb") as f:
            btxt = f.read().translate(None, b"\x0D\x1C\x1D\x1E\x1F")
        try:
            txt = btxt.decode("Latin-1")
            return cls.from_file(txt)
        except KeyError as err:
            raise KeyError(f"{err} missing in {path} for {cls.__name__}") from err
        except Exception as err:
            raise RuntimeError(f"{err} in {path} for {cls.__name__}") from err

    @classmethod
    def from_file(cls: Type[IB], text: str) -> IB:
        return converter_utc.structure(text, cls)

    def as_simple_dict(self) -> Dict[str, Any]:
        retval: Dict[str, Any] = converter_db.unstructure_attrs_asdict(self)
        return retval

    @classmethod
    def from_simple_tuple(cls: Type[IB], info: Tuple[Any, ...]) -> IB:
        return converter_db.structure(info, cls)

    def as_simple_tuple(self) -> Tuple[Any, ...]:
        retval: Tuple[Any, ...] = converter_db.unstructure_attrs_astuple(self)
        return retval

    @classmethod
    def get_field_names(cls) -> List[str]:
        return [f.name for f in attrs.fields(cls)]

    @classmethod
    def sqlite_create_table_statement(
        cls, name: str, constraint: Optional[Dict[str, str]] = None
    ) -> str:
        field_types = (type_as_sqlite(f.type) for f in attrs.fields(cls))
        names = cls.get_field_names()
        if constraint:
            field_types = (
                f"{f} {constraint[n]}" if n in constraint else f
                for n, f in zip(names, field_types)
            )
        columns = ", ".join(
            f"{name} {column}" for name, column in zip(names, field_types)
        )
        return f"CREATE TABLE {name} ({columns})"

    @classmethod
    def sqlite_insert_statement(cls, name: str) -> str:
        placeholders = ", ".join(["?"] * len(cls.get_field_names()))
        return f"INSERT INTO {name} VALUES ({placeholders});"


@attrs.define(kw_only=True, eq=True, frozen=True)
class Member(InfoBase):
    session_length: str = "default"
    status: str
    user_id: str
    format: str = "PlainText"
    hide: str = "Nothing"
    password: str = ""
    user_url: str = ""
    content: str = "Everything"
    email: str = ""
    old_email: str = ""
    name: str = ""
    email2: str = ""
    subscribe: str = ""
    alt_user_i_ds: str = ""


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCBase(InfoBase):
    content_type: ContentType = ContentType.Default
    title: str = ""
    body: Path
    url: URL = attrs.field(converter=convert_url)
    base_url: URL = attrs.field(converter=convert_url)
    responses: str
    date: datetime
    name: str = ""
    from_: Email = ""

    num_messages: Optional[int] = None
    footer_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    header_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    moderation: Optional[str] = None
    user_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    annotation_type: Optional[AnnotationType] = None


def convert_responses_to_num(self: "URCMain") -> str:
    return self.responses.lstrip("/")


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCMain(URCBase):
    list_address: str = ""
    categories: int
    num: str = attrs.field(
        default=attrs.Factory(convert_responses_to_num, takes_self=True)
    )

    default_outline_depth: Optional[int] = None

    # 'last_message_date', 'last_mod', 'up_url', 'list_address', 'categories', and 'num'
    up_url: Optional[URL] = attrs.field(converter=convert_url, default=None)
    last_message_date: Optional[datetime] = None
    last_mod: Optional[datetime] = None

    previous_num: Optional[int] = None


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCMessage(URCBase):
    last_message_date: datetime
    last_mod: datetime
    up_url: URL = attrs.field(converter=convert_url)

    num: int

    previous_num: Optional[int] = None
    next_num: Optional[int] = None
    keywords: None = None
    up_rel: Optional[str] = None
    node_type: Optional[str] = None
    newsgroups: Optional[URL] = attrs.field(converter=convert_url, default=None)

    message_id: str
