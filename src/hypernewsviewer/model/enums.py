from __future__ import annotations

import enum

__all__ = ["ContentType", "AnnotationType"]


class ContentType(enum.Enum):
    Default = enum.auto()
    PlainText = enum.auto()
    HTML = enum.auto()
    SmartText = enum.auto()
    WordProcessor = enum.auto()


class AnnotationType(enum.Enum):
    Default = enum.auto()
    Message = enum.auto()
