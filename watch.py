#!/usr/bin/env python3
"""Watch every byte of the drum's 0x30 report and report which ones move.

Run it, hit ONE zone repeatedly for a few seconds, then Ctrl-C. The summary
shows which byte indices changed, their range, and how many distinct values
they took -- that tells us digital (2 values) vs analog (many).
"""
import sys, time, collections
from hidlib import hid

VID, PID = 0x057E, 0x2009
N = 64


def main():
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    d = hid.Device(VID, PID)
    print(f"opened {d.product}. Watching {seconds}s -- HIT A ZONE NOW.\n")

    base = None
    seen = [collections.Counter() for _ in range(N)]
    nrep = 0
    t0 = time.time()
    try:
        while time.time() - t0 < seconds:
            r = d.read(N, timeout=200)
            if not r or r[0] != 0x30:
                continue
            nrep += 1
            if base is None:
                base = bytes(r)
            for i in range(min(N, len(r))):
                seen[i][r[i]] += 1
    except KeyboardInterrupt:
        pass
    d.close()

    print(f"{nrep} reports of 0x30\n")
    print(f"{'idx':>4} {'#vals':>6} {'min':>5} {'max':>5}  top values (value:count)")
    print("-" * 78)
    for i in range(N):
        vals = seen[i]
        if len(vals) <= 1:
            continue
        top = "  ".join(f"0x{v:02x}:{c}" for v, c in vals.most_common(6))
        print(f"{i:>4} {len(vals):>6} {min(vals):>5} {max(vals):>5}  {top}")

    print("\nbutton bytes 3,4,5 as bits (only values seen):")
    for i in (3, 4, 5):
        for v, c in sorted(seen[i].items()):
            print(f"  byte{i} = 0x{v:02x} {v:08b}  x{c}")


if __name__ == "__main__":
    main()
