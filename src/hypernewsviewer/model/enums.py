import enum

__all__ = ["ContentType", "AnnotationType"]


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return str(self.value)


class ContentType(StrEnum):
    HTML = "HTML"
    SmartText = "Smart Text"
    PlainText = "Plain Text"
    WordProcessor = "Word Processor"


class AnnotationType(StrEnum):
    Message = "Message"
