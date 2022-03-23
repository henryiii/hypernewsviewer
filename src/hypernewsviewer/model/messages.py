import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import attrs

from .converter import convert_url, converter_db, converter_utc, type_as_sqlite
from .enums import AnnotationType, ContentType, UpRelType

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
        columns = ",\n    ".join(
            f"{name} {column}" for name, column in zip(names, field_types)
        )
        return f"CREATE TABLE {name} (\n    {columns}\n);"

    @classmethod
    def sqlite_insert_statement(cls, name: str) -> str:
        placeholders = ", ".join(["?"] * len(cls.get_field_names()))
        return f"INSERT INTO {name} VALUES ({placeholders});"


@attrs.define(kw_only=True, eq=True, frozen=True)
class Member(InfoBase):
    user_id: str
    name: str = ""
    user_url: str = ""
    email: str = ""
    email2: str = ""

    alt_user_i_ds: str = ""
    content: str = "Everything"
    format: str = "PlainText"
    hide: str = "Nothing"
    old_email: str = ""
    # password: str = ""
    session_length: str = "default"
    status: str
    subscribe: str = ""


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCBase(InfoBase):
    responses: str

    title: str = ""
    date: datetime

    annotation_type: AnnotationType = AnnotationType.Default
    content_type: ContentType = ContentType.Default

    name: str = ""
    from_: Email = ""

    num_messages: Optional[int] = None

    @property
    def body(self) -> str:
        return f"{self.responses}-body.html"

    @property
    def url(self) -> str:
        return f"/get{self.responses}.html"

    @property
    def base_url(self) -> str:
        base = self.responses.strip("/").split("/")[0]
        return f"/get/{base}.html"

    @property
    def header_url(self) -> None:
        return None

    @property
    def footer_url(self) -> None:
        return None

    @property
    def user_url(self) -> None:
        return None

    @property
    def moderation(self) -> None:
        return None


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCMain(URCBase):
    list_address: str = ""
    categories: int

    last_message_date: Optional[datetime] = None
    last_mod: Optional[datetime] = None

    @property
    def num(self) -> str:
        return self.responses.lstrip("/")

    @property
    def default_outline_depth(self) -> None:
        return None

    @property
    def up_url(self) -> None:
        return None

    # Exactly one forum has this value, so it's not useful
    @property
    def previous_num(self) -> None:
        return None


@attrs.define(kw_only=True, eq=True, frozen=True)
class URCMessage(URCBase):
    last_message_date: datetime
    last_mod: datetime

    message_id: str
    num: int
    previous_num: Optional[int] = None
    next_num: Optional[int] = None

    up_url: URL = attrs.field(converter=convert_url)

    up_rel: UpRelType = UpRelType.Default
    node_type: AnnotationType = AnnotationType.Default

    @property
    def keywords(self) -> None:
        return None

    @property
    def newsgroups(self) -> URL:
        forum = self.responses.strip("/").split("/")[0]
        return f"/get/{forum}.html"
