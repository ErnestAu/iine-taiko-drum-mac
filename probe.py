#!/usr/bin/env python3
"""Probe the IINE taiko drum (Switch Pro Controller clone) for raw HID reports.

Passively reads for a few seconds. If the device is silent, runs the Switch Pro
Controller USB handshake and reads again.
"""
import sys, time, collections
from hidlib import hid

VID, PID = 0x057E, 0x2009


def drain(d, seconds, label):
    print(f"\n--- {label}: reading {seconds}s ---")
    counts = collections.Counter()
    samples = {}
    t0 = time.time()
    while time.time() - t0 < seconds:
        r = d.read(64, timeout=100)
        if not r:
            continue
        rid = r[0]
        counts[rid] += 1
        samples.setdefault(rid, bytes(r))
    if not counts:
        print("  (silent — no reports)")
        return counts
    for rid, n in counts.most_common():
        print(f"  report 0x{rid:02x}: {n} reports ({n/seconds:.0f}/s)")
        print(f"    first: {samples[rid].hex(' ')}")
    return counts


def send(d, data, label):
    try:
        n = d.write(bytes(data))
        print(f"  sent {label}: {n} bytes")
    except Exception as e:
        print(f"  FAILED {label}: {e}")
    time.sleep(0.1)


def main():
    d = hid.Device(VID, PID)
    print(f"opened: {d.manufacturer} / {d.product} / serial={d.serial}")
    d.nonblocking = False

    counts = drain(d, 3.0, "PASSIVE (no handshake)")

    if not counts:
        print("\n--- performing Switch Pro USB handshake ---")
        send(d, [0x80, 0x01], "0x80 0x01 (status/MAC)")
        send(d, [0x80, 0x02], "0x80 0x02 (handshake)")
        send(d, [0x80, 0x03], "0x80 0x03 (baudrate)")
        send(d, [0x80, 0x02], "0x80 0x02 (handshake again)")
        send(d, [0x80, 0x04], "0x80 0x04 (HID-only / no timeout)")
        drain(d, 3.0, "AFTER HANDSHAKE")

    d.close()


if __name__ == "__main__":
    main()
