#!/bin/bash
# Double-click to start using your taiko drum. Close the window to stop.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Taiko Drum isn't set up yet. Run the install line from the README first."
  exit 1
fi
.venv/bin/python -m taiko_drum start
echo
read -n 1 -s -r -p "Press any key to close this window."
