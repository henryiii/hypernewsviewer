from pathlib import Path

import pytest

from hypernewsviewer.model.messages import URCMessage
from hypernewsviewer.model.structure import AllForums

DIR = Path(__file__).parent.resolve()

HNFILES = DIR.parent.parent.joinpath("hnfiles")

if not HNFILES.exists():
    pytest.skip("No hnfiles directory found", allow_module_level=True)


def test_get_forums_iter():
    all_forums = AllForums(root=HNFILES)
    assert all_forums.get_num_forums() == 3

    forums = list(all_forums.get_forums_iter())
    assert len(forums) == 3

    forum = "hnTest"

    msgs = list(all_forums.get_msgs(forum, ""))
    assert len(msgs) == 688


def walk_tree_title(path: Path, _: str) -> str:
    return URCMessage.from_path(path).title


def test_recursive():
    all_forums = AllForums(root=HNFILES)
    forum = "hnTest"

    all_msgs = list(all_forums.walk_tree(forum, "", walk_tree_title, ""))
    assert len(all_msgs) == 876

    for msg in all_msgs:
        assert isinstance(msg, str)

    assert all_msgs == [m.title for m in all_forums.get_msgs(forum, "", recursive=True)]


def test_unique():
    all_forums = AllForums(root=HNFILES)
    forum = "hnTest"

    all_msgs = [m.responses for m in all_forums.get_msgs(forum, "", recursive=True)]
    assert len(all_msgs) == 876

    assert len(set(all_msgs)) == len(all_msgs)
    assert len(set(all_msgs)) == all_forums.get_num_msgs(forum, "", recursive=True)
