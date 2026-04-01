# HTML Live Wallpaper for GNOME (Oracle Linux 9 / RHEL 9 / Ubuntu)

Renders an animated HTML file as your desktop wallpaper using WebKit2GTK.

## How it works

1. **`html-wallpaper.py`** opens a GTK window with a WebKit2 browser engine inside it — the same engine Safari uses, so canvas animations, WebGL, etc. all work.

2. The window is set to `GDK_BACKEND=x11` which forces it through the X11 compatibility layer (XWayland on Wayland sessions, native on X11 sessions).

3. The window type is set to `_NET_WM_WINDOW_TYPE_DESKTOP` — this is the X11 hint that tells GNOME Shell "I am the desktop background". GNOME pins it below all other windows automatically. No xdotool, no window ID hunting, no hacks.

4. **`html-wallpaper.sh`** is a thin launcher that kills any existing instance and starts a new one. This is what the autostart entry calls.

5. The autostart `.desktop` file in `/etc/xdg/autostart/` (system-wide) or `~/.config/autostart/` (per-user) tells GNOME to launch the wallpaper 3 seconds after login. Because it runs inside the desktop session, `DISPLAY`, `XAUTHORITY`, and `DBUS_SESSION_BUS_ADDRESS` are all set automatically — no auth issues.

### Why not Firefox/Chromium?

Firefox and Chromium are separate processes — you can't control their window type hints. Previous attempts required xdotool to find the browser window and re-type it, which fails because:
- Firefox creates tooltip stub windows (200x200) that xdotool picks up instead
- Firefox crashes with D-Bus errors in kiosk mode on minimal installs
- GNOME repaints a white background over xdotool-pinned windows on login

WebKit2GTK avoids all of this because the browser engine is a *library embedded in our own window*, so we control every property directly.

---

## Quick start — single desktop

### Dependencies

**Oracle Linux 9 / RHEL 9:**
```bash
sudo dnf install -y python3 python3-gobject gtk3 webkit2gtk3
```

**Ubuntu / Debian:**
```bash
sudo apt install -y python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

### Run it

```bash
chmod +x html-wallpaper.sh html-wallpaper.py
./html-wallpaper.sh
```

That's it. The wallpaper appears behind all windows. `Ctrl+C` in the terminal to stop it.

### Survive login (current user only)

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/html-wallpaper.desktop << EOF
[Desktop Entry]
Type=Application
Name=HTML Wallpaper
Exec=$(pwd)/html-wallpaper.sh
Hidden=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=3
EOF
```

### Disable it

```bash
rm ~/.config/autostart/html-wallpaper.desktop
pkill -f html-wallpaper.py
```

---

## System-wide deploy — all users

Run `deploy-wallpaper.sh` as root:

```bash
sudo ./deploy-wallpaper.sh
```

This copies files to `/opt/html-wallpaper/` and creates `/etc/xdg/autostart/html-wallpaper.desktop`. Every user who logs into GNOME gets the wallpaper.

A user can opt out by copying the autostart file and disabling it:
```bash
cp /etc/xdg/autostart/html-wallpaper.desktop ~/.config/autostart/
sed -i 's/Hidden=false/Hidden=true/' ~/.config/autostart/html-wallpaper.desktop
```

---

## Kickstart — include in an existing Oracle Linux 9 build

### 1. Add the files to your USB/install media

```
usb/
├── ks.cfg                          # your existing kickstart
├── kickstart-wallpaper.ks
└── files/
    └── html-wallpaper/
        ├── html-wallpaper.py
        ├── html-wallpaper.sh
        ├── dt-a-v3-dynamic.html
        └── ShareTechMono-Regular.ttf   # optional — title font
```

### 2. Add one line to your existing `ks.cfg`

```
%include kickstart-wallpaper.ks
```

That's it. The kickstart snippet:
- Adds `python3`, `python3-gobject`, `gtk3`, and `webkit2gtk3` to `%packages`
- In `%post`, copies the files from the USB to `/opt/html-wallpaper/`
- Creates the system-wide autostart entry in `/etc/xdg/autostart/`
- Installs the font if present

### Note on the install media path

The kickstart assumes files are at `/run/install/isodir/files/html-wallpaper/`. If your install media mounts somewhere else, update the `SRC=` line in `kickstart-wallpaper.ks`.

---

## Air-gapped font note

The HTML references `Share Tech Mono` from Google Fonts. On air-gapped machines that request silently fails and text renders in a fallback monospace — everything works, the title just looks slightly different.

To get the exact font, download `ShareTechMono-Regular.ttf` on another machine and either:
- Drop it in the `files/html-wallpaper/` directory (kickstart installs it automatically)
- Or install manually: `cp ShareTechMono-Regular.ttf /usr/local/share/fonts/ && fc-cache -fv`

---

## Files

| File | What it does |
|---|---|
| `html-wallpaper.py` | Python script — WebKit2GTK browser in a DESKTOP-type window |
| `html-wallpaper.sh` | Launcher — kills old instance, starts new one |
| `dt-a-v3-dynamic.html` | The animated wallpaper |
| `deploy-wallpaper.sh` | System-wide installer (run as root) |
| `kickstart-wallpaper.ks` | Kickstart snippet — `%include` in your existing ks.cfg |
