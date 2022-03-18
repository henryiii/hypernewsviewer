import enum

__all__ = ["ContentType", "AnnotationType"]


class StrEnum(str, enum.Enum):
    def __str__(self) -> str:
        return str(self.value)


class ContentType(StrEnum):
    PlainText = "Plain Text"
    HTML = "HTML"
    SmartText = "Smart Text"
    WordProcessor = "Word Processor"
    PlainTex = "Plain Tex"


class AnnotationType(StrEnum):
    Message = "Message"
