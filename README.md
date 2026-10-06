# IINE Taiko Drum on Mac

**Got an IINE taiko drum and a Mac, and it just won't work? This fixes it.**

Your drum hits turn into key presses, so you can play taiko games in your web
browser, like [taikoapp.uk](https://taikoapp.uk). Works on MacBooks and other Macs.

| Hit the drum here | It types |
|---|---|
| Left side of the middle (don) | **F** |
| Right side of the middle (don) | **J** |
| Left rim (ka) | **D** |
| Right rim (ka) | **K** |

## What you need

- An IINE taiko drum (the kind made for Nintendo Switch and PC)
- Its USB cable, plus a USB-C adapter if your Mac only has USB-C ports
  (the cheap kind is fine)

## Set it up (once, about 5 minutes)

1. Open **Terminal**: press **Command + Space**, type **Terminal**, then press **Return**.
2. Copy this line, paste it into Terminal, and press **Return**:

   ```
   curl -fsSL https://raw.githubusercontent.com/ErnestAu/iine-taiko-drum-mac/main/install.sh | bash
   ```

   If a window pops up asking to install **command line developer tools**,
   click **Install**, wait for it to finish, then paste the line again.
3. When Terminal says **Done!**, you'll find **Start Taiko Drum** on your Desktop.

## Play

1. Plug in your drum.
2. Double-click **Start Taiko Drum** on your Desktop.
3. **First time only:** your Mac asks if Terminal can control your computer.
   Click **Open System Settings**, turn on the switch next to **Terminal**,
   then quit Terminal (**Command + Q**) and double-click **Start Taiko Drum** again.
4. When it says **Drum connected!**, open your game and play.
   To stop, close the window.

Click on the game before you start playing, so it's the one hearing your keys.

## Something not working?

Open your home folder (in Finder, press **Command + Shift + H**), open
**Taiko Drum**, and double-click **Check Taiko Drum**. It checks your setup and
has you hit each part of the drum, without typing anything.

- **The drum types nonstop, or goes haywire:** another controller app is
  running, usually **Enjoyable**. Quit it.
- **Soft hits don't count:** that's the drum itself. It ignores light taps, so
  hit firmly, near the middle of each part. Drum rolls made of light bouncing
  taps won't register on this drum.
- **Nothing happens in the game:** click on the game first, then play.
- **"Drum plugged in ✗":** unplug the drum and plug it back in firmly, or try
  another port or adapter.

## Why didn't my drum just work?

The drum pretends to be a Nintendo Switch controller, and it describes its own
data wrongly. Apps like Enjoyable believe that description, so they see buttons
being pressed nonstop. Browser controller testers don't see the drum at all.
Swapping USB adapters doesn't help, because the adapter was never the problem.

This tool skips the drum's description and reads the real data directly. The
full story is in [How it works](docs/HOW-IT-WORKS.md).

## Uninstall

Delete the **Taiko Drum** folder in your home folder, and **Start Taiko Drum**
on your Desktop.

## Other drums

So far this works with the IINE drum, which shows up as a "Pro Controller".
Support for other drums is planned. If yours doesn't work, please
[open an issue](https://github.com/ErnestAu/iine-taiko-drum-mac/issues) and say
which drum you have.

## For developers

Python 3.9+, one dependency (`hidapi`). After running `install.sh` from a clone:

```
.venv/bin/python -m taiko_drum check     # test the drum, types nothing
.venv/bin/python -m taiko_drum start     # play
.venv/bin/python -m unittest             # run the tests
```

The code is in [`taiko_drum/`](taiko_drum/). The investigation scripts used to
work out the drum's data are in this repo's first commit.

## License

[MIT](LICENSE)
