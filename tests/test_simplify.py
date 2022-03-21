from pathlib import Path

import attrs
import pytest

from hypernewsviewer.model.messages import URCMessage, simplifiy_message
from hypernewsviewer.model.structure import AllForums

DIR = Path(__file__).parent.resolve()

HNFILES = DIR.parent.parent.joinpath("hnfiles")

if not HNFILES.exists():
    pytest.skip("No hnfiles directory found")


def test_simplify():
    all_forums = AllForums(root=HNFILES)
    forum = "hnTest"

    all_msgs = list(all_forums.get_msgs(forum, "", recursive=True))
    simple_msgs = [simplifiy_message(m) for m in all_msgs]

    for orig, simp in zip(all_msgs, simple_msgs):
        for field in attrs.fields(URCMessage):  # pylint: disable=not-an-iterable
            assert getattr(orig, field.name) == getattr(
                simp, field.name
            ), f"{field.name} differs for {orig.responses}"
