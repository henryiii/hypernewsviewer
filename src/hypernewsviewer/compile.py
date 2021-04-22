from __future__ import annotations

from pathlib import Path

import sass

DIR = Path(__file__).parent.resolve()
STATIC = DIR / "static"


def main() -> None:
    sass.compile(dirname=(STATIC / "scss", STATIC / "css"), output_style="compressed")


if __name__ == "__main__":
    main()
