# pylint: disable=redefined-outer-name

import contextlib
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from hypernewsviewer.model.structure import AllForums, DBForums

DIR = Path(__file__).parent.resolve()
ROOT = DIR.joinpath("../../hnfiles").resolve()


@pytest.fixture(scope="session")
def db(tmp_path_factory):
    directory = tmp_path_factory.mktemp("tmpdb")
    path = directory / "tmpdb.sql3"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "hypernewsviewer.model",
            f"--db={path}",
            "all",
            "populate",
        ],
        check=True,
    )
    with contextlib.closing(sqlite3.connect(path)) as con:
        yield con


def test_basic(db):
    with contextlib.closing(db.cursor()) as cur:
        cur.execute("SELECT COUNT(*) FROM forums")
        assert cur.fetchone()[0] == 3
        cur.execute("SELECT COUNT(*) FROM msgs")
        assert cur.fetchone()[0] == 2717
        cur.execute("SELECT COUNT(*) FROM people")
        assert cur.fetchone()[0] == 7017

        results = list(x[0] for x in cur.execute("SELECT user_id FROM people"))
        more_than_one = {n: v for n, v in Counter(results).items() if v > 1}
        assert not more_than_one


def test_get_msg(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_msg("hnTest", "1")
    classic_results = forums.get_msg("hnTest", "1")
    assert classic_results == results

    results = dbf.get_msg("hnTest", "1/1")
    classic_results = forums.get_msg("hnTest", "1/1")
    assert classic_results == results

    results = dbf.get_msg("hnTest", "688")
    classic_results = forums.get_msg("hnTest", "688")
    assert classic_results == results


def test_get_msgs(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = list(dbf.get_msgs("hnTest", ""))
    classic_results = list(forums.get_msgs("hnTest", ""))
    assert [r.responses for r in results] == [r.responses for r in classic_results]
    assert len(results) == 688
    assert len(classic_results) == 688
    assert classic_results == results

    results = list(dbf.get_msgs("hnTest", ""))
    classic_results = list(forums.get_msgs("hnTest", ""))
    assert [r.responses for r in results] == [r.responses for r in classic_results]
    assert len(results) == 688
    assert len(classic_results) == 688
    assert classic_results == results

    results = list(dbf.get_msgs("hnTest", "6"))
    classic_results = list(forums.get_msgs("hnTest", "6"))
    assert len(results) == 3
    assert len(classic_results) == 3
    assert classic_results == results

    results = list(dbf.get_msgs("hnTest", "6", recursive=True))
    classic_results = list(forums.get_msgs("hnTest", "6", recursive=True))
    assert len(results) == 4
    assert classic_results == results

    results = list(dbf.get_msgs("hnTest", "6/1", recursive=True))
    classic_results = list(forums.get_msgs("hnTest", "6/1"))
    assert len(results) == 1
    assert classic_results == results


def test_get_msg_paths(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = list(dbf.get_msg_paths("hnTest", ""))
    classic_results = list(forums.get_msg_paths("hnTest", ""))
    assert len(results) == 688
    assert len(classic_results) == 688
    assert classic_results == results

    results = list(dbf.get_msg_paths("hnTest", "6"))
    classic_results = list(forums.get_msg_paths("hnTest", "6"))
    assert len(results) == 3
    assert len(classic_results) == 3
    assert classic_results == results

    results = list(dbf.get_msg_paths("hnTest", "6/1"))
    classic_results = list(forums.get_msg_paths("hnTest", "6/1"))
    assert len(results) == 1
    assert classic_results == results


def test_get_num_msgs(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_num_msgs("hnTest", "")
    classic_results = forums.get_num_msgs("hnTest", "")
    assert classic_results == 688
    assert results == 688

    results = dbf.get_num_msgs("hnTest", "", recursive=True)
    classic_results = forums.get_num_msgs("hnTest", "", recursive=True)
    assert classic_results == 876
    assert results == 876

    assert dbf.get_num_msgs("hnTest", "6") == 3
    assert forums.get_num_msgs("hnTest", "6") == 3

    assert dbf.get_num_msgs("hnTest", "6", recursive=True) == 4
    assert forums.get_num_msgs("hnTest", "6", recursive=True) == 4

    assert dbf.get_num_msgs("hnTest", "6/1") == 1
    assert forums.get_num_msgs("hnTest", "6/1") == 1

    assert dbf.get_num_msgs("hnTest", "6/1", recursive=True) == 1
    assert forums.get_num_msgs("hnTest", "6/1", recursive=True) == 1


def test_get_member(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_member("temple")
    classic_results = forums.get_member("temple")
    assert classic_results == results


def test_get_members_paths(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = sorted(dbf.get_members_paths())
    classic_results = sorted(forums.get_members_paths())
    assert classic_results == results
    assert len(results) == 7017
    assert len(classic_results) == 7017


def test_get_members_iter(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = list(dbf.get_member_iter())
    classic_results = list(forums.get_member_iter())
    assert classic_results == results
    assert len(results) == 7017
    assert len(classic_results) == 7017


def test_get_num_members(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_num_members()
    classic_results = forums.get_num_members()
    assert classic_results == results
    assert results == 7017


def test_get_forum(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_forum("hnTest")
    classic_results = forums.get_forum("hnTest")
    assert classic_results == results


def test_get_forums_iter(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = list(dbf.get_forums_iter())
    classic_results = list(forums.get_forums_iter())
    assert [r.num for r in results] == [r.num for r in classic_results]
    assert classic_results == results
    assert len(results) == 3


def test_get_forum_paths(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = sorted(dbf.get_forum_paths())
    classic_results = sorted(forums.get_forum_paths())
    assert classic_results == results
    assert len(results) == 3


def test_get_num_forums(db):
    forums = AllForums(root=ROOT)
    dbf = DBForums(root=ROOT, db=db)

    results = dbf.get_num_forums()
    classic_results = forums.get_num_forums()
    assert classic_results == results
    assert results == 3
