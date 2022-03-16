import sqlite3

import rich.pretty
import rich.traceback

from hypernewsviewer.model.messages import Member, URCMain, URCMessage
from hypernewsviewer.model.structure import AllForums, DBForums

__all__ = [
    "db",
    "cur",
    "forums",
    "Member",
    "URCMain",
    "URCMessage",
    "AllForums",
    "DBForums",
]

rich.pretty.install()
rich.traceback.install()

db = sqlite3.connect("hnvdb.sql3")
cur = db.cursor()

forums = AllForums(root="../hnfiles")
