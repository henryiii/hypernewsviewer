from __future__ import annotations

from typing import TextIO

import click
import rich.traceback
from rich import print

from .parser import Kind, URCMain, URCMessage

rich.traceback.install(show_locals=True)


@click.command()
@click.argument("input_file", type=click.File("r", lazy=True), nargs=-1)
@click.option("--kind", type=click.Choice(Kind), required=True)
def main(input_file: list[TextIO], kind: Kind) -> None:
    URC = URCMain if kind == Kind.main else URCMessage
    for ifile in input_file:
        with ifile as file:
            urc = URC.from_file(file)
            print(urc)


if __name__ == "__main__":
    main()
