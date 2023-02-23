# pylint: disable=redefined-outer-name

import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import sqlalchemy
import sqlalchemy.orm

from hypernewsviewer.model.structure import AllForums, DBForums

DIR = Path(__file__).parent.resolve()
HNFILES = DIR.joinpath("../../hnfiles").resolve()

if not HNFILES.exists():
    pytest.skip("No hnfiles directory found", allow_module_level=True)


@pytest.fixture(scope="session")
def db(tmp_path_factory):
    directory = tmp_path_factory.mktemp("tmpdb")
    path = directory / "tmpdb.sql3"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "hypernewsviewer.model",
            f"--db={path}",
            "populate",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        msg = "Failed to populate database, see output above"
        raise RuntimeError(msg)

    return sqlalchemy.create_engine(f"sqlite:///{path}", future=True, echo=True)


def test_basic(db):
    with db.connect() as connection:
        result = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM forums"))
        assert result.scalar_one() == 3

        result = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM msgs"))
        assert result.scalar_one() == 2717

        result = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM people"))
        assert result.scalar_one() == 7017

        result = connection.execute(sqlalchemy.text("SELECT user_id FROM people"))
        results = list(result.scalars())
        assert len(results) == 7017

        more_than_one = {n: v for n, v in Counter(results).items() if v > 1}
        assert not more_than_one


def test_get_msg(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

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
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

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
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

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
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

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
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = dbf.get_member("temple")
    classic_results = forums.get_member("temple")
    assert classic_results == results


def test_get_members_paths(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = sorted(dbf.get_members_paths())
    classic_results = sorted(forums.get_members_paths())
    assert classic_results == results
    assert len(results) == 7017
    assert len(classic_results) == 7017


def test_get_members_iter(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = list(dbf.get_member_iter())
    classic_results = list(forums.get_member_iter())
    assert classic_results == results
    assert len(results) == 7017
    assert len(classic_results) == 7017


def test_get_num_members(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = dbf.get_num_members()
    classic_results = forums.get_num_members()
    assert classic_results == results
    assert results == 7017


def test_get_forum(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = dbf.get_forum("hnTest")
    classic_results = forums.get_forum("hnTest")
    assert classic_results == results


def test_get_forums_iter(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = list(dbf.get_forums_iter())
    classic_results = list(forums.get_forums_iter())
    assert [r.num for r in results] == [r.num for r in classic_results]
    assert classic_results == results
    assert len(results) == 3


def test_get_forum_paths(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = sorted(dbf.get_forum_paths())
    classic_results = sorted(forums.get_forum_paths())
    assert len(results) == 3
    assert classic_results == results


def test_get_num_forums(db):
    forums = AllForums(root=HNFILES)
    dbf = DBForums(root=HNFILES, engine=db)

    results = dbf.get_num_forums()
    classic_results = forums.get_num_forums()
    assert classic_results == results
    assert results == 3
