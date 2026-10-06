"""Tests for reading the drum, using report bytes captured from the real thing.

Run with:  .venv/bin/python -m unittest
"""
import unittest

from taiko_drum.drum import (
    LEFT_DON, LEFT_KA, RIGHT_DON, RIGHT_KA,
    Drum, DrumUnplugged, Event, changes, zones_held,
)

# A real idle report (ID 0x30) from the drum: timer in byte 1, buttons in
# bytes 3-5 (byte 4's 0x80 bit is always on), sticks centered, motion data static.
IDLE = bytes.fromhex(
    "30 f3 81 00 80 00 00 f8 7f 00 f8 7f 0c 00 00 00 00 fa 0f 00 00 00 00 00 00 00 00 00"
    " 00 fa 0f 00 00 00 00 00 00 00 00 00 00 fa 0f 00 00 00 00 00 00 00 00 00 00 00 00 00"
    " 00 00 00 00 00 00 00 00"
)


def with_bytes(report=IDLE, **changes_by_index):
    """Copy of a report with some bytes replaced, e.g. with_bytes(b4=0x88)."""
    out = bytearray(report)
    for key, value in changes_by_index.items():
        out[int(key[1:])] = value
    return bytes(out)


# Each zone as captured: one bit, set while that part of the drum is struck.
HIT = {
    LEFT_DON: with_bytes(b4=0x88),
    RIGHT_DON: with_bytes(b4=0x84),
    LEFT_KA: with_bytes(b5=0x80),
    RIGHT_KA: with_bytes(b3=0x80),
}


class ZonesHeldTest(unittest.TestCase):
    def test_idle_drum_has_nothing_pressed(self):
        self.assertEqual(zones_held(IDLE), frozenset())

    def test_each_zone_is_read_from_its_own_bit(self):
        for zone, report in HIT.items():
            with self.subTest(zone=zone.name):
                self.assertEqual(zones_held(report), {zone})

    def test_both_dons_at_once(self):
        self.assertEqual(zones_held(with_bytes(b4=0x8C)), {LEFT_DON, RIGHT_DON})

    def test_the_ticking_timer_byte_is_never_read_as_a_hit(self):
        # Generic gamepad tools read byte 1 (a counter that changes every
        # report) as buttons, which is why they see the drum firing nonstop.
        for tick in range(256):
            self.assertEqual(zones_held(with_bytes(b1=tick)), frozenset())


class ChangesTest(unittest.TestCase):
    def test_strike_then_release(self):
        self.assertEqual(changes(frozenset(), {LEFT_DON}), [Event(LEFT_DON, True)])
        self.assertEqual(changes({LEFT_DON}, frozenset()), [Event(LEFT_DON, False)])

    def test_holding_a_zone_produces_no_new_events(self):
        self.assertEqual(changes({LEFT_DON}, {LEFT_DON}), [])


class FakeDevice:
    """Stands in for the USB device: returns the given reports, then unplugs."""

    def __init__(self, reports):
        self._reports = list(reports)

    def read(self, size, timeout_ms):
        if not self._reports:
            raise OSError("read error")
        return list(self._reports.pop(0))

    def close(self):
        pass


class DrumEventsTest(unittest.TestCase):
    def events_from(self, reports):
        seen = []
        with self.assertRaises(DrumUnplugged):
            for event in Drum(FakeDevice(reports)).events():
                seen.append(event)
        return seen

    def test_a_strike_held_across_reports_is_one_press(self):
        # The drum holds each strike for 80 ms, i.e. about 10 reports.
        reports = [IDLE] + [HIT[LEFT_DON]] * 10 + [IDLE]
        self.assertEqual(
            self.events_from(reports),
            [Event(LEFT_DON, True), Event(LEFT_DON, False)],
        )

    def test_read_timeouts_are_skipped(self):
        self.assertEqual(
            self.events_from([b"", HIT[RIGHT_KA], b"", IDLE]),
            [Event(RIGHT_KA, True), Event(RIGHT_KA, False)],
        )

    def test_reports_other_than_0x30_are_ignored(self):
        # 0x21 is a reply to a configuration command, not drum input.
        reply = bytes([0x21]) + HIT[LEFT_DON][1:]
        self.assertEqual(self.events_from([IDLE, reply, IDLE]), [])

    def test_unplugging_leaves_held_zones_visible_for_cleanup(self):
        drum = Drum(FakeDevice([HIT[LEFT_KA]]))
        with self.assertRaises(DrumUnplugged):
            list(drum.events())
        self.assertEqual(drum.held, {LEFT_KA})


if __name__ == "__main__":
    unittest.main()
