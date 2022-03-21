from __future__ import annotations

import enum

__all__ = ["ContentType", "AnnotationType"]


class StrEnum(str, enum.Enum):
    def __repr__(self) -> str:
        return str(self.value)


class ContentType(StrEnum):
    Default = "d"
    PlainText = "p"
    HTML = "h"
    SmartText = "s"
    WordProcessor = "w"


class AnnotationType(StrEnum):
    Default = "d"
    Message = "m"
