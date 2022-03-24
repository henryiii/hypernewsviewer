from __future__ import annotations

import enum

__all__ = ["ContentType", "AnnotationType", "UpRelType"]


class StrEnum(str, enum.Enum):
    pass


class ContentType(StrEnum):
    Default = "d"
    PlainText = "p"
    HTML = "h"
    SmartText = "s"
    WordProcessor = "w"


class AnnotationType(StrEnum):
    Default = "d"
    Message = "m"


class UpRelType(StrEnum):
    Default = "Default"  # If not specified, this is the default
    None_ = "None"
    News = "News"
    Warning = "Warning"
    Feedback = "Feedback"
    Question = "Question"
    More = "More"
    Disagree = "Disagree"
    Note = "Note"
    Ok = "Ok"
    Angry = "Angry"
    Agree = "Agree"
    Idea = "Idea"
    Sad = "Sad"
