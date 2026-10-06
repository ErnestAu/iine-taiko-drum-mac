#!/bin/bash
# Installs Taiko Drum for Mac. Safe to run again: it updates in place.
#
#   curl -fsSL https://raw.githubusercontent.com/ErnestAu/iine-taiko-drum-mac/main/install.sh | bash
set -euo pipefail

REPO="ErnestAu/iine-taiko-drum-mac"
DEST="$HOME/Taiko Drum"

step() { printf '\n==> %s\n' "$1"; }

# Python comes with Apple's free Command Line Tools.
if ! xcode-select -p >/dev/null 2>&1; then
  cat <<'MSG'

Your Mac needs Apple's free developer tools first.
A window will pop up: click "Install" and wait for it to finish.
Then paste the install line into Terminal again.
MSG
  xcode-select --install >/dev/null 2>&1 || true
  exit 1
fi

# Run from a downloaded copy of the project? Set it up right there.
# Otherwise (piped from curl), download the latest version.
HERE=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [ -n "$HERE" ] && [ -d "$HERE/taiko_drum" ]; then
  DEST="$HERE"
else
  step "Downloading"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$TMP"
  mkdir -p "$DEST"
  rm -rf "$DEST/taiko_drum"
  cp -R "$TMP"/*/. "$DEST/"
fi

step "Setting up (about a minute the first time)"
/usr/bin/python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/python" -m pip install --quiet --upgrade pip
"$DEST/.venv/bin/python" -m pip install --quiet -r "$DEST/requirements.txt"
chmod +x "$DEST"/*.command

# Put a launcher on the Desktop so there's nothing to go looking for.
if [ -d "$HOME/Desktop" ]; then
  LAUNCHER="$HOME/Desktop/Start Taiko Drum.command"
  printf '#!/bin/bash\nexec "%s/Start Taiko Drum.command"\n' "$DEST" > "$LAUNCHER"
  chmod +x "$LAUNCHER"
fi

cat <<MSG

Done! Installed in: $DEST

Plug in your drum, then double-click "Start Taiko Drum" on your Desktop.
MSG
