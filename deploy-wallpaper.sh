#!/usr/bin/env bash
# deploy-wallpaper.sh — Install the HTML wallpaper system-wide on Oracle Linux 9.
# Run as root. Every user who logs into GNOME gets the animated wallpaper.
set -euo pipefail

INSTALL_DIR="/opt/html-wallpaper"
AUTOSTART_DIR="/etc/xdg/autostart"
FONT_DIR="/usr/local/share/fonts"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing HTML wallpaper ==="

# 1. Dependencies
echo "[1/4] Installing dependencies..."
dnf install -y python3 python3-gobject gtk3 webkit2gtk3 2>/dev/null || {
    echo "WARN: dnf install failed — packages may already be installed or you need EPEL."
    echo "      Try: dnf install -y epel-release && dnf install -y webkit2gtk3"
}

# 2. Install files
echo "[2/4] Copying files to ${INSTALL_DIR}..."
mkdir -p "$INSTALL_DIR"
cp "$SCRIPT_DIR/html-wallpaper.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/dt-a-v3-dynamic.html" "$INSTALL_DIR/"

cat > "$INSTALL_DIR/html-wallpaper.sh" << 'LAUNCHER'
#!/usr/bin/env bash
# Kill any previous instance for this user, then launch.
pkill -u "$(id -u)" -f 'html-wallpaper.py' 2>/dev/null || true
sleep 0.3
exec python3 /opt/html-wallpaper/html-wallpaper.py /opt/html-wallpaper/dt-a-v3-dynamic.html
LAUNCHER

chmod 755 "$INSTALL_DIR/html-wallpaper.sh"
chmod 755 "$INSTALL_DIR/html-wallpaper.py"
chmod 644 "$INSTALL_DIR/dt-a-v3-dynamic.html"

# 3. System-wide autostart
echo "[3/4] Creating autostart entry..."
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/html-wallpaper.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=HTML Wallpaper
Comment=Animated HTML desktop wallpaper (system-wide)
Exec=/opt/html-wallpaper/html-wallpaper.sh
Hidden=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
DESKTOP

# 4. Font (optional — install if present)
echo "[4/4] Checking for font..."
if [ -f "$SCRIPT_DIR/ShareTechMono-Regular.ttf" ]; then
    mkdir -p "$FONT_DIR"
    cp "$SCRIPT_DIR/ShareTechMono-Regular.ttf" "$FONT_DIR/"
    fc-cache -f 2>/dev/null || true
    echo "      Installed Share Tech Mono font."
else
    echo "      ShareTechMono-Regular.ttf not found — wallpaper will use fallback monospace."
    echo "      (This is cosmetic only, everything still works.)"
fi

echo ""
echo "=== Done ==="
echo "Every GNOME user (local, IPA, LDAP) will get the wallpaper on next login."
echo "To test now:  /opt/html-wallpaper/html-wallpaper.sh"
echo "To disable per-user: copy /etc/xdg/autostart/html-wallpaper.desktop to"
echo "  ~/.config/autostart/ and set Hidden=true"
