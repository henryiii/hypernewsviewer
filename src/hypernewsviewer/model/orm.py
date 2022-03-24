from __future__ import annotations

import datetime
from typing import Any, TypeVar

import attrs
import sqlalchemy
import sqlalchemy.orm

mapper_registry = sqlalchemy.orm.registry()

T = TypeVar("T")


def type_as_sqal(
    name: str, inp: type[Any] | None, metadata: dict[str, Any]
) -> sqlalchemy.Column:
    assert inp is not None
    options = dict(metadata.items())
    try:
        options["nullable"] = isinstance(None, inp)
    except TypeError:
        # Python < 3.10 doesn't support this on Optional - but that's okay, we now know it is Optional!
        options["nullable"] = True
        (inp,) = (t for t in inp.__args__ if not isinstance(None, t))
    assert inp is not None

    if isinstance(1, inp):
        return sqlalchemy.Column(name, sqlalchemy.Integer, **options)

    if isinstance(1.0, inp):
        return sqlalchemy.Column(name, sqlalchemy.Float, **options)

    if isinstance(datetime.datetime.now(), inp):
        return sqlalchemy.Column(name, sqlalchemy.DateTime, **options)

    if hasattr(inp, "__members__"):
        return sqlalchemy.Column(
            name,
            sqlalchemy.Enum(inp, values_callable=lambda x: [e.value for e in x]),
            **options,
        )

    return sqlalchemy.Column(name, sqlalchemy.String, **options)


class attrs_mapper:
    def __init__(self, table_name: str, registry: Any) -> None:
        self.table_name = table_name
        self.registry = registry

    def __call__(self, attrs_class: type[T]) -> type[T]:
        columns = (
            type_as_sqal(f.name, f.type, f.metadata) for f in attrs.fields(attrs_class)
        )
        attrs_class.__table__ = sqlalchemy.Table(  # type: ignore[attr-defined]
            self.table_name,
            self.registry.metadata,
            # Column("id", Integer, primary_key=True),
            *columns,
        )
        return self.registry.mapped(attrs_class)  # type: ignore[no-any-return]
