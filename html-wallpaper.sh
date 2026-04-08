#!/usr/bin/env bash
# html-wallpaper.sh — Launch the HTML wallpaper.
# Usage: html-wallpaper.sh [path-to-html]
#
# This runs from a GNOME autostart .desktop file, which means the session
# environment (DISPLAY, XAUTHORITY, DBUS_SESSION_BUS_ADDRESS) is already
# set. We just need to kill any old instance and launch.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="${1:-$SCRIPT_DIR/dt-a-v3-dynamic.html}"

# Kill any previous instance
pkill -f 'html-wallpaper.py' 2>/dev/null
sleep 0.5

# Strip snap/flatpak library paths that break GTK imports when launched
# from inside a snap terminal (e.g. VS Code). Harmless on clean systems.
exec env -i \
  HOME="$HOME" \
  DISPLAY="${DISPLAY:-:0}" \
  XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}" \
  DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" \
  XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  PATH="/usr/local/bin:/usr/bin:/bin" \
  python3 "$SCRIPT_DIR/html-wallpaper.py" "$HTML"
