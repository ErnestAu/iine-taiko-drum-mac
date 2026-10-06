"""Turn your IINE taiko drum into a keyboard.

    python -m taiko_drum start    play: drum hits type F, J, D and K
    python -m taiko_drum check    test the drum without typing anything
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

from . import keyboard
from .drum import ZONES, Drum, DrumNotFound, DrumUnplugged, is_plugged_in

NOT_FOUND_HELP = """
Your Mac can't see the drum. Try these:
  - Unplug the drum and plug it back in firmly, adapter included.
  - Try a different USB port or USB-C adapter.
  - Then run this again."""


def app_name() -> str:
    """The app macOS will ask permission for: whichever one is running us."""
    return {
        "Apple_Terminal": "Terminal",
        "iTerm.app": "iTerm",
        "vscode": "Visual Studio Code",
    }.get(os.environ.get("TERM_PROGRAM", ""), "Terminal")


def permission_help() -> str:
    app = app_name()
    return f"""
One-time setup: macOS needs your OK before the drum can type keys.

  1. A macOS window just popped up. Click "Open System Settings".
     (No window? Open System Settings > Privacy & Security > Accessibility.)
  2. Turn ON the switch next to "{app}".
  3. Quit {app} completely (press Cmd+Q), then start the drum again."""


def enjoyable_running() -> bool:
    """Enjoyable misreads this drum and fires keys nonstop, fighting us."""
    return subprocess.run(["pgrep", "-x", "Enjoyable"], capture_output=True).returncode == 0


def wait_for_drum() -> None:
    if not is_plugged_in():
        print("Waiting for your drum... plug it in.")
        while not is_plugged_in():
            time.sleep(1)


def start() -> int:
    if not keyboard.can_type():
        keyboard.ask_permission()
        print(permission_help())
        return 1
    if enjoyable_running():
        print("Heads up: Enjoyable is running. Quit it, or your hits will go haywire.\n")

    down: set[int] = set()  # keycodes we're holding, so we never leave one stuck
    try:
        while True:
            wait_for_drum()
            try:
                with Drum() as drum:
                    print("Drum connected! Open your taiko game in the browser and play.")
                    print("   " + "   ".join(f"{z.name} = {z.key}" for z in ZONES))
                    print("To stop, close this window.\n")
                    hits = 0
                    for event in drum.events():
                        code = event.zone.keycode
                        if event.pressed:
                            keyboard.key_down(code)
                            down.add(code)
                            hits += 1
                            print(f"\r   {hits} hits (last: {event.zone.name})    ", end="", flush=True)
                        else:
                            keyboard.key_up(code)
                            down.discard(code)
            except (DrumNotFound, DrumUnplugged):
                for code in down:
                    keyboard.key_up(code)
                down.clear()
                print("\n\nThe drum was disconnected.")
                time.sleep(1)
    except KeyboardInterrupt:
        return 0
    finally:
        for code in down:
            keyboard.key_up(code)


def check() -> int:
    plugged, can_type = is_plugged_in(), keyboard.can_type()
    print("Checking your setup...\n")
    print(f"  {'✓' if plugged else '✗'} Drum plugged in")
    print(f"  {'✓' if can_type else '✗'} Allowed to type keys")
    if enjoyable_running():
        print("  ✗ Enjoyable is running. Quit it, it conflicts with the drum.")
    if not plugged:
        print(NOT_FOUND_HELP)
        return 1

    print("\nNow hit each part of the drum once. Nothing gets typed during this test.\n")
    remaining = list(ZONES)
    try:
        with Drum() as drum:
            for event in drum.events():
                if event.pressed and event.zone in remaining:
                    remaining.remove(event.zone)
                    print(f"  ✓ {event.zone.name:<10} types {event.zone.key}")
                    if not remaining:
                        break
    except (DrumNotFound, DrumUnplugged):
        print("\nThe drum was disconnected during the test.")
        return 1
    except KeyboardInterrupt:
        print("\n\nStopped. Never felt a hit on: " + ", ".join(z.name for z in remaining))
        return 1

    print("\nAll four parts of the drum work!")
    if not can_type:
        print("Last step: start the drum, and it will walk you through allowing it to type.")
    return 0


def _stop(signum, frame):
    raise KeyboardInterrupt


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    # Closing the Terminal window sends SIGHUP. Treat it like Ctrl-C so any held
    # key is released instead of staying stuck down.
    signal.signal(signal.SIGHUP, _stop)
    signal.signal(signal.SIGTERM, _stop)
    command = argv[0] if argv else "start"
    if command == "start":
        return start()
    if command == "check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
