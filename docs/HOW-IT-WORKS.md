# How it works

Notes from reverse-engineering the IINE taiko drum on macOS. You don't need any
of this to use the drum. It's here for the curious, and for anyone adapting this
project to a different drum.

## What the drum really is

Over USB the drum says it's a **Nintendo Switch Pro Controller**
(vendor `0x057E`, product `0x2009`). It isn't a PlayStation controller, and it
isn't a keyboard. Your Mac recognizes it as a joystick.

It sends a 64-byte update called an input report (ID `0x30`) **125 times a
second**, with no setup needed:

```
30 f3 81 00 80 00 00 f8 7f 00 f8 7f 0c 00 00 00 00 fa 0f ...
   ^^ timer  ^^^^^^^^ buttons  ^^^^^^^^^^^^^^^^^ sticks, always centered
```

| Byte | Contents |
|---|---|
| 0 | Report ID, `0x30` |
| 1 | Timer that counts up with every report |
| 3–5 | Buttons, one bit each. The drum hits live here. |
| 6–11 | Two thumbsticks, which never move |
| 13+ | Motion sensors, which are fake: always the same values |

## The four drum zones

Each zone is one bit:

| Zone | Pretends to be | Byte | Bit | Types |
|---|---|---|---|---|
| Left don (center) | Left stick click | 4 | `0x08` | F |
| Right don (center) | Right stick click | 4 | `0x04` | J |
| Left ka (rim) | ZL | 5 | `0x80` | D |
| Right ka (rim) | ZR | 3 | `0x80` | K |

Byte 4's `0x80` bit is always on, and it means nothing.

## Why other tools don't work

**Enjoyable and other gamepad-to-keyboard apps fire nonstop.** Every USB device
describes its own data layout, and this drum describes its layout wrongly. Read
the way the drum describes it, the "buttons" fall on byte 1, the timer, which
changes 125 times a second. So those apps see every button pressing and
releasing constantly. It looks like sensor noise, but it isn't, and a deadzone
or sensitivity setting can't fix it. This project ignores the drum's
self-description and reads the bytes where they actually are.

**Gamepad testers in the browser don't see the drum at all.** Chrome handles
Switch Pro Controllers with special code that expects the real controller's
startup handshake. That's the most likely reason this clone never shows up.

**A different USB adapter won't help.** The drum works fine through a basic
USB-A to USB-C adapter. The problem was always how the data gets read.

## Timing and sensitivity limits

These are properties of the drum's own firmware. No software can change them.

- **Each hit is one clean 80 ms press.** The drum decides inside its own chip
  whether you hit hard enough, then reports a simple on or off. There's no
  pressure value anywhere in the data, and no bouncing or double-triggering.
- **Light taps that the drum rejects are invisible.** They produce no data at
  all, so buzz rolls (light bouncing taps) don't register. Strike firmly and
  near the center of each pad.
- **One zone tops out at about 12 hits per second.** A second hit inside the
  same 80 ms window gets merged into the first. Alternating hands gets you to
  about 25 per second.
- **The mode switch (holding buttons while plugging in) changed nothing** on the
  drum this was built with. It reported exactly the same data every time.

## macOS permissions

Only **Accessibility** is needed, so that the drum can type keys. Input
Monitoring isn't needed: macOS only guards keyboard-type devices, and this drum
reads fine without it.

## Adapting this to a different drum

If your drum reports a different vendor or product ID, or different bytes, the
original investigation scripts can help you map it. They're in this repo's first
commit:

- `probe.py` lists what the device sends
- `watch.py` shows which bytes change while you hit a zone
- `map_zones.py` names each button as you hit it

Then update `ZONES` in [`taiko_drum/drum.py`](../taiko_drum/drum.py).
