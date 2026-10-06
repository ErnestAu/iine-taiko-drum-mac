#!/usr/bin/env python3
"""IINE taiko drum -> keyboard, for taikoapp.uk and other browser taiko games.

The drum enumerates as a Nintendo Switch Pro Controller clone (VID 0x057E,
PID 0x2009) and streams input report 0x30 at 125 Hz over USB with no handshake.
Its HID *report descriptor* is generic and does not match that report's real
layout -- laid over the actual bytes, the descriptor's "buttons" land on byte 1,
a free-running timer. That is why generic HID remappers (Enjoyable and friends)
see every button chattering at 125 Hz. This script ignores the descriptor and
parses report 0x30 directly.

The four hit zones are plain digital buttons in bytes 3-5. Each strike produces
exactly one press held for a firmware-fixed 80 ms, already debounced in
hardware, so no deadzone, hysteresis, or retrigger lockout is needed here.

SENSITIVITY IS FIRMWARE AND CANNOT BE CHANGED FROM HERE -- measured, not assumed:
  - Under sustained hard hitting, the only bytes that ever move are the timer
    (byte 1) and the button bits. Sticks stay pinned at 00 f8 7f, IMU static.
  - The controller-mode combo (hold left+right while plugging in) was tried
    three times: identical VID/PID, report ID, and payload every time.
  - The drum does answer real Pro Controller subcommands (observed a 0x21 ACK to
    an SPI read), but that protocol has no pad-sensitivity command, and its two
    input modes (0x30 full / 0x3F simple) differ only in volume, not expressivity.
So the drum decides what counts as a hit and sends one bit. A tap below its
threshold puts NO bytes on the wire -- there is nothing here to be sensitive to.
Consequences: buzz rolls (light bounced taps) do not work at all, and one zone
cannot exceed 12.5 hits/sec (~25/sec alternating). Both are hardware ceilings.
The USB dongle is NOT implicated -- we read the device through it at 125 Hz.

    zone              button   byte/bit    key
    left  don/center  L3       4 / 0x08    F
    right don/center  R3       4 / 0x04    J
    left  ka/rim      ZL       5 / 0x80    D
    right ka/rim      ZR       3 / 0x80    K

Usage:
    python3 taiko_mapper.py monitor        # print hits, send nothing (safe)
    python3 taiko_mapper.py run            # send keystrokes
    python3 taiko_mapper.py run --pulse 20 # release each key 20ms after pressing
    python3 taiko_mapper.py run --repeat   # recover firmware-merged roll hits

Note on sensitivity: the drum decides in firmware what counts as a hit and sends
only one bit, so nothing here can make it notice a lighter tap -- a rejected tap
puts no bytes on the wire. --pulse only shortens the emitted keypress (helps if
the game wants a keyup before the next keydown). --repeat recovers hits the drum
DID detect but folded into one 80 ms pulse; it never invents rejected ones.

macOS permissions -- grant to your *terminal app*, then fully quit and reopen it
(permissions do not apply to already-running processes):
    Input Monitoring   to read the drum
    Accessibility      to synthesize keystrokes ("run" only)
"""
import os
import sys
import time

from hidlib import hid

VID, PID = 0x057E, 0x2009
REPORT_ID = 0x30

# (byte index, bit mask) -> (zone label, macOS ANSI virtual keycode, key label)
ZONES = {
    (4, 0x08): ("left don  (center)", 3, "F"),
    (4, 0x04): ("right don (center)", 38, "J"),
    (5, 0x80): ("left ka   (rim)", 2, "D"),
    (3, 0x80): ("right ka  (rim)", 40, "K"),
}


def held_zones(report):
    """Set of zone keys currently pressed in a 0x30 report."""
    return {k for k in ZONES if report[k[0]] & k[1]}


class Keyboard:
    """Synthesizes key events at the HID event tap via Quartz."""

    def __init__(self):
        from Quartz import (
            CGEventCreateKeyboardEvent,
            CGEventPost,
            CGEventSetFlags,
            kCGHIDEventTap,
        )
        self._create = CGEventCreateKeyboardEvent
        self._post = CGEventPost
        self._set_flags = CGEventSetFlags
        self._tap = kCGHIDEventTap

    @staticmethod
    def is_trusted():
        """True if this process has Accessibility permission."""
        import ctypes, ctypes.util

        try:
            lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ApplicationServices"))
            lib.AXIsProcessTrusted.restype = ctypes.c_bool
            lib.AXIsProcessTrusted.argtypes = []
            return lib.AXIsProcessTrusted()
        except Exception:
            return True  # can't tell; let the user find out by trying

    def send(self, keycode, down):
        ev = self._create(None, keycode, down)
        # Clear inherited modifiers so a held Shift/Cmd can't corrupt the key.
        self._set_flags(ev, 0)
        self._post(self._tap, ev)


def open_drum():
    try:
        return hid.Device(VID, PID)
    except Exception as e:
        sys.exit(
            f"could not open the drum ({e}).\n"
            "  - is it plugged in? check with: ioreg -r -c IOHIDDevice -l | grep -i 'pro controller'\n"
            "  - has your terminal been granted Input Monitoring, then fully quit and reopened?"
        )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "monitor"
    if mode not in ("monitor", "run"):
        sys.exit(__doc__)

    # --pulse N: release the key N ms after pressing it, instead of mirroring the
    # drum's 80 ms hold. This cannot make the drum notice lighter hits -- it only
    # helps if the *game* is gated on seeing a keyup before the next keydown.
    pulse_ms = None
    if "--pulse" in sys.argv:
        pulse_ms = float(sys.argv[sys.argv.index("--pulse") + 1])

    # --repeat: the firmware holds a zone's bit high for a fixed 80 ms window, and
    # a second hit landing inside that window extends the high by another window
    # instead of emitting a new pulse. Those merged hits were really struck, so
    # emit one extra keystroke per extra window to recover them. This does NOT
    # invent hits the drum rejected -- only ones it detected and folded together.
    # Threshold sits BETWEEN the 80 ms quanta, not on one. We only observe a
    # release on the next 125 Hz report, so an ordinary 80 ms pulse can look like
    # 90-110 ms; comparing against 80 would fire on that jitter and invent hits
    # that were never struck. A real merge holds for a full 160 ms.
    repeat_ms = None
    if "--repeat" in sys.argv:
        i = sys.argv.index("--repeat") + 1
        repeat_ms = float(sys.argv[i]) if i < len(sys.argv) and not sys.argv[i].startswith("-") else 120.0

    kb = None
    if mode == "run":
        kb = Keyboard()
        if not kb.is_trusted():
            sys.exit(
                "Accessibility permission is not granted, so keystrokes would go nowhere.\n"
                "Grant it to your terminal app in System Settings > Privacy & Security >\n"
                "Accessibility, then FULLY QUIT and reopen the terminal and try again.\n"
                "(Use `monitor` mode meanwhile -- it needs no Accessibility.)"
            )

    d = open_drum()
    print(f"opened {d.manufacturer} / {d.product}")
    if mode == "run":
        print("sending keystrokes -- focus taikoapp.uk now.  Ctrl-C to stop.\n")
    else:
        print("monitor mode: printing hits, sending nothing.  Ctrl-C to stop.\n")

    prev = set()
    counts = {k: 0 for k in ZONES}
    emitted = {}    # zone -> time we sent keydown, for keys still logically down
    last_hit = {}   # zone -> time of its most recent keystroke, while hw-held
    t0 = time.time()
    try:
        while True:
            r = d.read(64, timeout=500)
            now = time.time()

            if r and r[0] == REPORT_ID:
                cur = held_zones(r)
                for k in cur - prev:
                    zone, keycode, key = ZONES[k]
                    counts[k] += 1
                    if kb:
                        kb.send(keycode, True)
                    emitted[k] = last_hit[k] = now
                    print(f"{now - t0:>8.3f}s  {zone:<19} -> {key}")
                for k in prev - cur:
                    last_hit.pop(k, None)
                    # Skip if a --pulse timeout already released this key.
                    if k in emitted:
                        if kb:
                            kb.send(ZONES[k][1], False)
                        del emitted[k]
                prev = cur

            # A zone still high one full window after its last keystroke means the
            # firmware merged another real hit into this pulse. Emit it.
            if repeat_ms is not None:
                for k, t in list(last_hit.items()):
                    if (now - t) * 1000 >= repeat_ms:
                        zone, keycode, key = ZONES[k]
                        counts[k] += 1
                        if kb:
                            if k in emitted:
                                kb.send(keycode, False)
                            kb.send(keycode, True)
                        emitted[k] = last_hit[k] = now
                        print(f"{now - t0:>8.3f}s  {zone:<19} -> {key}  (merged)")

            if pulse_ms is not None:
                for k, t in list(emitted.items()):
                    if (now - t) * 1000 >= pulse_ms:
                        if kb:
                            kb.send(ZONES[k][1], False)
                        del emitted[k]
    except KeyboardInterrupt:
        pass
    finally:
        # Never leave a key stuck down.
        if kb:
            for k in emitted:
                kb.send(ZONES[k][1], False)
        d.close()

    total = sum(counts.values())
    print(f"\n{total} hits in {time.time() - t0:.1f}s")
    for k, n in counts.items():
        print(f"  {ZONES[k][0]:<19} {n}")


if __name__ == "__main__":
    main()
