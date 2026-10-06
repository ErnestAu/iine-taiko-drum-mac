#!/usr/bin/env python3
"""Measure the drum's pulse width and hit rate under a fast roll.

We know a single deliberate strike gives an 80 ms pulse. The open question is
whether that 80 ms is FIXED (hard ceiling of ~12 hits/sec on one zone, and fast
double-hits get swallowed) or ADAPTIVE (firmware shortens it under fast play, so
the ceiling is higher than it looks).

Roll as fast as you can on ONE zone for the whole window, then read the pulse
width distribution.

Usage:  python3 rolltest.py [seconds]
"""
import sys
import time

from hidlib import hid

VID, PID = 0x057E, 0x2009
ZONES = {
    (4, 0x08): "left don",
    (4, 0x04): "right don",
    (5, 0x80): "left ka",
    (3, 0x80): "right ka",
}


def held(report):
    return {k for k in ZONES if report[k[0]] & k[1]}


def stats(name, xs):
    if not xs:
        return
    xs = sorted(xs)
    mid = xs[len(xs) // 2]
    print(f"    {name:<22} n={len(xs):<4} min={xs[0]:>6.1f}  med={mid:>6.1f}  max={xs[-1]:>6.1f} ms")


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    d = hid.Device(VID, PID)
    print(f"opened {d.product}")
    print(f"ROLL AS FAST AS YOU CAN on ONE zone for {seconds}s. Go.\n")

    prev = set()
    down_at, last_down = {}, {}
    widths = {k: [] for k in ZONES}     # how long the bit stayed high
    gaps = {k: [] for k in ZONES}       # press-to-press interval
    t0 = time.time()
    try:
        while time.time() - t0 < seconds:
            r = d.read(64, timeout=200)
            if not r or r[0] != 0x30:
                continue
            now = time.time()
            cur = held(r)
            for k in cur - prev:
                if k in last_down:
                    gaps[k].append((now - last_down[k]) * 1000)
                down_at[k] = last_down[k] = now
            for k in prev - cur:
                if k in down_at:
                    widths[k].append((now - down_at[k]) * 1000)
            prev = cur
    except KeyboardInterrupt:
        pass
    d.close()

    elapsed = time.time() - t0
    print(f"{elapsed:.1f}s elapsed\n")
    for k, label in ZONES.items():
        n = len(widths[k])
        if not n:
            continue
        print(f"  {label}  --  {n} hits, {n / elapsed:.1f}/sec")
        stats("pulse width", widths[k])
        stats("press-to-press gap", gaps[k])
        print()

    # Pulse widths land on multiples of ~80 ms: the firmware holds the bit high
    # for a fixed 80 ms window, and a hit landing inside that window extends the
    # high by another window rather than emitting a fresh pulse. So check whether
    # widths are QUANTIZED at 80 ms, not merely whether they vary -- a merged
    # double-hit looks like "varying" width but means the opposite.
    allw = [w for k in ZONES for w in widths[k]]
    if allw:
        QUANTUM = 80.0
        resid = [min(w % QUANTUM, QUANTUM - (w % QUANTUM)) for w in allw]
        merged = sum(1 for w in allw if w >= 1.5 * QUANTUM)
        print(f"pulse widths as multiples of {QUANTUM:.0f}ms: "
              + ", ".join(f"{w / QUANTUM:.2f}x" for w in sorted(allw)))
        if max(resid) < 15:
            print(f"  -> FIXED {QUANTUM:.0f}ms pulse, quantized. Hard firmware ceiling.")
            if merged:
                print(f"  -> {merged} pulse(s) span >1 window: hits the firmware MERGED.")
                print("     Recover those with:  taiko_mapper.py run --repeat")
        else:
            print("  -> widths are not quantized; firmware may genuinely adapt.")


if __name__ == "__main__":
    main()
