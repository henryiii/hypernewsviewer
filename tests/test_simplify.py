from pathlib import Path
from typing import Any

import attrs
import pytest

from hypernewsviewer.model.converter import produce_utc_dict
from hypernewsviewer.model.messages import URCMessage
from hypernewsviewer.model.structure import AllForums

DIR = Path(__file__).parent.resolve()

HNFILES = DIR.parent.parent.joinpath("hnfiles")

if not HNFILES.exists():
    pytest.skip("No hnfiles directory found", allow_module_level=True)


def missed(path: Path) -> dict[str, Any]:
    obj = path.read_text(encoding="Latin-1")
    info = produce_utc_dict(obj)
    fields = attrs.fields_dict(URCMessage)
    return {
        n: v.replace("https://hypernews.cern.ch/HyperNews/CMS", "")
        for n, v in info.items()
        if n not in fields
    }


def test_simplify():
    all_forums = AllForums(root=HNFILES)
    forum = "hnTest"

    all_msgs = [URCMessage.from_path(p) for p in all_forums.get_msg_paths(forum, "")]
    raw_msgs = [missed(p) for p in all_forums.get_msg_paths(forum, "")]

    for orig, simp in zip(all_msgs, raw_msgs):
        for name in simp:
            assert (
                getattr(orig, name) == simp[name]
            ), f"{name} differs for {orig.responses}"
