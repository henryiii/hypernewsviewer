from pathlib import Path

import attrs
import pytest

from hypernewsviewer.model.messages import Message, URCMessage
from hypernewsviewer.model.structure import AllForums

DIR = Path(__file__).parent.resolve()

HNFILES = DIR.parent.parent.joinpath("hnfiles")

if not HNFILES.exists():
    pytest.skip("No hnfiles directory found")


def test_simplify():
    all_forums = AllForums(root=HNFILES)
    forum = "hnTest"

    all_msgs = [URCMessage.from_path(p) for p in all_forums.get_msg_paths(forum, "")]
    simple_msgs = [Message.from_path(p) for p in all_forums.get_msg_paths(forum, "")]

    for orig, simp in zip(all_msgs, simple_msgs):
        for field in attrs.fields(URCMessage):  # pylint: disable=not-an-iterable
            assert getattr(orig, field.name) == getattr(
                simp, field.name
            ), f"{field.name} differs for {orig.responses}"
