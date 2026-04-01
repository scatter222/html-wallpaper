# ──────────────────────────────────────────────────────────────────────────────
# kickstart-wallpaper.ks — HTML animated wallpaper for Oracle Linux 9
#
# Include this in your main kickstart:
#   %include kickstart-wallpaper.ks
#
# Expects these files alongside the kickstart on the install media:
#   files/html-wallpaper/
#   ├── html-wallpaper.py
#   ├── html-wallpaper.sh
#   ├── dt-a-v3-dynamic.html
#   └── ShareTechMono-Regular.ttf   (optional — font for title text)
# ──────────────────────────────────────────────────────────────────────────────

%packages
python3
python3-gobject
gtk3
webkit2gtk3
%end

%post --log=/root/kickstart-wallpaper.log

# ── Copy wallpaper files from install media ──────────────────────────────────
SRC="/run/install/isodir/files/html-wallpaper"

mkdir -p /opt/html-wallpaper
cp "$SRC/html-wallpaper.py"       /opt/html-wallpaper/
cp "$SRC/html-wallpaper.sh"       /opt/html-wallpaper/
cp "$SRC/dt-a-v3-dynamic.html"    /opt/html-wallpaper/

chmod 755 /opt/html-wallpaper/html-wallpaper.py
chmod 755 /opt/html-wallpaper/html-wallpaper.sh
chmod 644 /opt/html-wallpaper/dt-a-v3-dynamic.html

# Font (optional)
if [ -f "$SRC/ShareTechMono-Regular.ttf" ]; then
    mkdir -p /usr/local/share/fonts
    cp "$SRC/ShareTechMono-Regular.ttf" /usr/local/share/fonts/
    fc-cache -f 2>/dev/null || true
fi

# ── System-wide GNOME autostart ──────────────────────────────────────────────
mkdir -p /etc/xdg/autostart
cat > /etc/xdg/autostart/html-wallpaper.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=HTML Wallpaper
Comment=Animated HTML desktop wallpaper (system-wide)
Exec=/opt/html-wallpaper/html-wallpaper.sh
Hidden=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
EOF

echo "html-wallpaper: installed."

%end
