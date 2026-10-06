#!/usr/bin/env python3
"""Live button-edge log for the IINE taiko drum (Switch Pro Controller clone).

Prints every press/release as it happens, with the decoded button name, how
long the press lasted, and the gap since the previous event. Hit ONE zone at a
time, deliberately, and read the mapping straight off the output.

Usage:  DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 map_zones.py [seconds]
"""
import sys, time
from hidlib import hid

VID, PID = 0x057E, 0x2009

# Standard Switch Pro Controller button bitfield, report 0x30 bytes 3/4/5.
BUTTONS = {
    3: ["Y", "X", "B", "A", "SR-r", "SL-r", "R", "ZR"],
    4: ["Minus", "Plus", "R3", "L3", "Home", "Capture", "?4.6", "ChargingGrip"],
    5: ["Down", "Up", "Right", "Left", "SR-l", "SL-l", "L", "ZL"],
}
# Bits that are pinned on by this clone and carry no information.
IGNORE = {(4, 7)}


def bits(report):
    """Set of (byte_index, bit) currently held, minus the pinned ones."""
    held = set()
    for bi in (3, 4, 5):
        v = report[bi]
        for bit in range(8):
            if v & (1 << bit) and (bi, bit) not in IGNORE:
                held.add((bi, bit))
    return held


def name(key):
    bi, bit = key
    return f"{BUTTONS[bi][bit]} (byte{bi} bit{bit} = 0x{1 << bit:02x})"


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
    d = hid.Device(VID, PID)
    print(f"opened {d.product}.  Logging {seconds}s.")
    print("Hit ONE zone at a time, pausing between zones.\n")
    print(f"{'time':>8}  {'event':<7} {'button':<34} {'held':>7}  {'gap':>7}")
    print("-" * 72)

    prev = set()
    down_at = {}
    last_event = None
    t0 = time.time()
    npress = 0
    try:
        while time.time() - t0 < seconds:
            r = d.read(64, timeout=200)
            if not r or r[0] != 0x30:
                continue
            now = time.time()
            cur = bits(r)

            for k in cur - prev:
                gap = f"{(now - last_event) * 1000:.0f}ms" if last_event else "-"
                print(f"{now - t0:>7.3f}s  {'PRESS':<7} {name(k):<34} {'':>7}  {gap:>7}")
                down_at[k] = now
                last_event = now
                npress += 1
            for k in prev - cur:
                held = (now - down_at.get(k, now)) * 1000
                gap = f"{(now - last_event) * 1000:.0f}ms" if last_event else "-"
                print(f"{now - t0:>7.3f}s  {'release':<7} {name(k):<34} {held:>6.0f}ms  {gap:>7}")
                last_event = now
            prev = cur
    except KeyboardInterrupt:
        pass
    d.close()
    print(f"\n{npress} presses total.")


if __name__ == "__main__":
    main()
