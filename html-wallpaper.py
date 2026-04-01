#!/usr/bin/env python3
"""
html-wallpaper.py — Render an HTML file as a live GNOME desktop wallpaper.

Uses WebKit2GTK in an X11 window with _NET_WM_WINDOW_TYPE_DESKTOP,
which GNOME Shell pins below all other windows.
"""

import os
import sys
import signal
import gi

os.environ["GDK_BACKEND"] = "x11"

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

for wk_ver in ("4.1", "4.0"):
    try:
        gi.require_version("WebKit2", wk_ver)
        break
    except ValueError:
        continue
else:
    print("Error: WebKit2GTK not found. Install webkit2gtk3 (dnf) or "
          "gir1.2-webkit2-4.1 (apt).", file=sys.stderr)
    sys.exit(1)

from gi.repository import Gtk, Gdk, WebKit2, GLib


def get_html_path():
    if len(sys.argv) > 1:
        p = os.path.abspath(sys.argv[1])
    else:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "dt-a-v3-dynamic.html")
    if not os.path.isfile(p):
        print(f"Error: HTML file not found: {p}", file=sys.stderr)
        sys.exit(1)
    return p


def has_real_gpu():
    """
    Return True if a non-software GPU is available.
    llvmpipe / softpipe are Mesa software renderers — they will burn CPU
    doing full-screen canvas compositing.  On a server with no discrete GPU
    we want software rendering OFF so WebKit uses its own CPU canvas path,
    which is far more efficient than software GL.
    """
    try:
        import subprocess
        out = subprocess.check_output(
            ["glxinfo", "-B"], stderr=subprocess.DEVNULL, text=True, timeout=3
        )
        # Software renderers
        software = ("llvmpipe", "softpipe", "swr", "software rasterizer",
                    "VMware SVGA", "virgl")
        renderer_line = next(
            (l for l in out.splitlines() if "OpenGL renderer" in l), ""
        )
        print(f"GL renderer: {renderer_line.strip()}", flush=True)
        return not any(s.lower() in renderer_line.lower() for s in software)
    except Exception as e:
        print(f"GPU check failed ({e}) — assuming no real GPU", flush=True)
        return False


def main():
    html_path = get_html_path()
    html_uri  = f"file://{html_path}"

    display = Gdk.Display.get_default()
    if display is None:
        print("Error: cannot connect to display.", file=sys.stderr)
        sys.exit(1)

    monitor = display.get_primary_monitor() or display.get_monitor(0)
    geom    = monitor.get_geometry()
    scale   = monitor.get_scale_factor()
    print(f"Screen: {geom.width}x{geom.height}  scale={scale}", flush=True)

    # ── Window ──────────────────────────────────────────────────────────────
    win = Gtk.Window(title="html-wallpaper")
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.set_accept_focus(False)
    win.set_default_size(geom.width, geom.height)
    win.move(geom.x, geom.y)
    win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)

    # ── WebKit settings ──────────────────────────────────────────────────────
    webview  = WebKit2.WebView()
    settings = webview.get_settings()

    settings.set_enable_javascript(True)
    settings.set_enable_webgl(True)
    settings.set_enable_write_console_messages_to_stdout(True)

    # ── FIX: Hardware acceleration policy ───────────────────────────────────
    # ALWAYS forces Mesa llvmpipe software GL on servers with no discrete GPU.
    # llvmpipe rasterising a 60fps full-screen canvas animation uses every CPU
    # core flat-out.  ON_DEMAND lets WebKit decide — on a real GPU it uses it,
    # on a server it falls back to WebKit's own CPU canvas path which is
    # purpose-built for 2D and far cheaper than software GL.
    gpu = has_real_gpu()
    if gpu:
        policy = WebKit2.HardwareAccelerationPolicy.ALWAYS
        print("Real GPU detected — hardware acceleration ON", flush=True)
    else:
        policy = WebKit2.HardwareAccelerationPolicy.ON_DEMAND
        print("No real GPU — hardware acceleration ON_DEMAND (avoids llvmpipe)", flush=True)

    settings.set_hardware_acceleration_policy(policy)
    webview.set_settings(settings)

    webview.set_background_color(Gdk.RGBA(0, 0, 0, 1))
    win.add(webview)
    webview.load_uri(html_uri)
    print(f"Loading: {html_uri}", flush=True)

    win.connect("destroy", lambda *_: Gtk.main_quit())
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, Gtk.main_quit)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT,  Gtk.main_quit)

    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
