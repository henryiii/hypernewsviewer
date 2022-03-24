import os
from datetime import datetime
from typing import List, Optional, Type, TypeVar

import attrs

from .enums import AnnotationType, ContentType, UpRelType
from .orm import attrs_mapper, mapper_registry

Email = str
URL = str

IB = TypeVar("IB", bound="InfoBase")


@attrs.define(kw_only=True, eq=True, slots=False)
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
        # pylint: disable-next=import-outside-toplevel
        from .converter import converter_utc

        return converter_utc.structure(text, cls)

    @classmethod
    def get_field_names(cls) -> List[str]:
        return [f.name for f in attrs.fields(cls)]


@attrs_mapper("people", mapper_registry)
@attrs.define(kw_only=True, eq=True, slots=False)
class Member(InfoBase):
    "Registered user information"
    user_id: str = attrs.field(metadata={"primary_key": True})
    name: str = ""
    user_url: str = ""
    email: str = ""
    email2: str = ""

    alt_user_i_ds: str = ""
    content: str = "Everything"
    format: ContentType = ContentType.PlainText
    hide: str = "Nothing"
    old_email: str = ""
    # password: str = ""
    session_length: str = "default"
    status: str
    subscribe: str = ""


@attrs.define(kw_only=True, eq=True, slots=False)
class URCBase(InfoBase):
    responses: str = attrs.field(metadata={"primary_key": True})

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


@attrs_mapper("forums", mapper_registry)
@attrs.define(kw_only=True, eq=True, slots=False)
class URCMain(URCBase):
    "Forum information"
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


@attrs_mapper("msgs", mapper_registry)
@attrs.define(kw_only=True, eq=True, slots=False)
class URCMessage(URCBase):
    "Individual message information"
    last_message_date: datetime
    last_mod: datetime

    message_id: str
    num: int
    previous_num: Optional[int] = None
    next_num: Optional[int] = None

    up_url: URL = attrs.field(metadata={"index": True})

    up_rel: UpRelType = UpRelType.Default
    node_type: AnnotationType = AnnotationType.Default

    @property
    def keywords(self) -> None:
        return None

    @property
    def newsgroups(self) -> URL:
        forum = self.responses.strip("/").split("/")[0]
        return f"/get/{forum}.html"
