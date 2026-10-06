"""Reading the IINE taiko drum over USB.

The drum identifies itself as a Nintendo Switch Pro Controller and streams a
64-byte input report (ID 0x30) 125 times a second. The four drum zones are
single bits in bytes 3-5 of that report. See docs/HOW-IT-WORKS.md for how this
was worked out, and why generic gamepad tools misread the drum.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import hid

VENDOR_ID = 0x057E   # Nintendo
PRODUCT_ID = 0x2009  # Switch Pro Controller
INPUT_REPORT = 0x30  # the "full input" report the drum streams


@dataclass(frozen=True)
class Zone:
    name: str      # what the player hits, e.g. "left don"
    byte: int      # which byte of the report holds it
    mask: int      # which bit of that byte
    key: str       # the key it types
    keycode: int   # macOS virtual keycode for that key


LEFT_DON = Zone("left don", 4, 0x08, "F", 3)
RIGHT_DON = Zone("right don", 4, 0x04, "J", 38)
LEFT_KA = Zone("left ka", 5, 0x80, "D", 2)
RIGHT_KA = Zone("right ka", 3, 0x80, "K", 40)
ZONES = (LEFT_DON, RIGHT_DON, LEFT_KA, RIGHT_KA)


@dataclass(frozen=True)
class Event:
    zone: Zone
    pressed: bool  # True when the zone is struck, False when it lets go


class DrumNotFound(Exception):
    pass


class DrumUnplugged(Exception):
    pass


def zones_held(report: bytes) -> frozenset[Zone]:
    """Zones currently pressed, given one 0x30 input report."""
    return frozenset(z for z in ZONES if report[z.byte] & z.mask)


def changes(before: frozenset[Zone], after: frozenset[Zone]) -> list[Event]:
    """Strikes and releases between two consecutive reports, in ZONES order."""
    return [Event(z, True) for z in ZONES if z in after and z not in before] + [
        Event(z, False) for z in ZONES if z in before and z not in after
    ]


def is_plugged_in() -> bool:
    return bool(hid.enumerate(VENDOR_ID, PRODUCT_ID))


class Drum:
    """An open connection to the drum. Use as a context manager."""

    def __init__(self, device=None):
        if device is None:
            device = hid.device()
            try:
                device.open(VENDOR_ID, PRODUCT_ID)
            except OSError as e:
                raise DrumNotFound() from e
        self._device = device
        self.held: frozenset[Zone] = frozenset()

    def events(self) -> Iterator[Event]:
        """Yield an Event for every strike and release. Runs until unplugged."""
        while True:
            try:
                report = self._device.read(64, 500)
            except OSError as e:
                raise DrumUnplugged() from e
            # Other report IDs are replies to configuration commands; skip them.
            if report and report[0] == INPUT_REPORT:
                now = zones_held(report)
                yield from changes(self.held, now)
                self.held = now

    def close(self) -> None:
        self._device.close()

    def __enter__(self) -> Drum:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
