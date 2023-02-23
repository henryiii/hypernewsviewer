from __future__ import annotations

import sys

if sys.version_info < (3, 10):
    from typing_extensions import Concatenate, ParamSpec
else:
    from typing import Concatenate, ParamSpec

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

__all__ = ["Concatenate", "ParamSpec", "Self"]
