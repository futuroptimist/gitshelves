"""Compatibility shim for SCAD generation helpers."""

from __future__ import annotations

import sys
import types

from .render import scad as _scad

for _name in dir(_scad):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_scad, _name)

__all__ = getattr(
    _scad,
    "__all__",
    [name for name in globals() if not name.startswith("__") and name != "_scad"],
)


class _Shim(types.ModuleType):
    def __getattr__(self, name: str):
        return getattr(_scad, name)

    def __setattr__(self, name: str, value):
        if name in {"_scad", "__all__"}:
            super().__setattr__(name, value)
            return
        setattr(_scad, name, value)
        super().__setattr__(name, value)


sys.modules[__name__].__class__ = _Shim
