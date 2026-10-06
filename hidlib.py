"""Shared hidapi import for the taiko scripts.

The `hid` package dlopens libhidapi at import time. Homebrew installs it under
/opt/homebrew/lib (Apple Silicon) or /usr/local/lib (Intel), neither of which is
on the default dyld search path, so a plain `python3 script.py` fails. Setting
DYLD_LIBRARY_PATH after the process has started is too late -- dyld reads it at
launch -- so re-exec ourselves once with it set.

Use as:  from hidlib import hid
"""
import os
import sys

_LIB_DIRS = ("/opt/homebrew/lib", "/usr/local/lib")
_FLAG = "_TAIKO_REEXEC"

try:
    import hid
except Exception:
    if os.environ.get(_FLAG):
        raise  # already retried; the library is genuinely missing
    existing = os.environ.get("DYLD_LIBRARY_PATH", "")
    os.environ["DYLD_LIBRARY_PATH"] = ":".join(
        [d for d in _LIB_DIRS if os.path.isdir(d)] + ([existing] if existing else [])
    )
    os.environ[_FLAG] = "1"
    os.execv(sys.executable, [sys.executable] + sys.argv)

__all__ = ["hid"]
