import sqlite3

import rich.pretty
import rich.traceback

from hypernewsviewer.model.messages import Member, Message, URCMain, URCMessage
from hypernewsviewer.model.structure import AllForums, DBForums

__all__ = [
    "AllForums",
    "DBForums",
    "Member",
    "Message",
    "URCMain",
    "URCMessage",
    "cur",
    "db",
    "forums",
]

rich.pretty.install()
rich.traceback.install()

db = sqlite3.connect("hnvdb.sql3")
cur = db.cursor()

forums = AllForums(root="../hnfiles")
