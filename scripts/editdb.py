"""
Usage: Run with -i to interact with the database.

For example:

    py -m IPython -i scripts/editdb.py
"""


import rich.pretty
import rich.syntax
import rich.table
import rich.traceback
import sqlalchemy
import sqlalchemy.orm
from rich import print  # pylint: disable=redefined-builtin
from sqlalchemy import select

from hypernewsviewer.model.messages import Member, URCMain, URCMessage
from hypernewsviewer.model.structure import AllForums, DBForums

__all__ = [
    "AllForums",
    "DBForums",
    "Member",
    "URCMain",
    "URCMessage",
    "engine",
    "file_forums",
    "forums",
    "Session",
    "select",
]

rich.pretty.install()
rich.traceback.install(show_locals=True, width=None)

engine = sqlalchemy.create_engine("sqlite:///hnvdb.sql3", future=True, echo=True)
forums = DBForums(root="../hnfiles", engine=engine)
file_forums = AllForums(root="../hnfiles")

Session = sqlalchemy.orm.sessionmaker(engine)

EXAMPLE = """\
with Session() as session:
     selection = sqlalchemy.select(Member).where(Member.user_id.like("elmer"))
     results = list(session.execute(selection).scalars())
print(results)"""

print("[bold]Available database ORM objects:")
table = rich.table.Table("Name", "Description")
for item in [Member, URCMain, URCMessage]:
    table.add_row(item.__name__, item.__doc__)
print(table)

print("[bold]Example of usage:")
print(rich.syntax.Syntax(EXAMPLE, lexer="python", theme="default"))
