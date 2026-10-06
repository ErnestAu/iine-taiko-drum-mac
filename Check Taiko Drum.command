#!/bin/bash
# Double-click to test your drum. Nothing gets typed during the test.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Taiko Drum isn't set up yet. Run the install line from the README first."
  exit 1
fi
.venv/bin/python -m taiko_drum check
echo
read -n 1 -s -r -p "Press any key to close this window."
