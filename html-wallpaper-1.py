#!/usr/bin/env python3
"""
html-wallpaper.py — Render an HTML file as a live GNOME desktop wallpaper.
WebKit2GTK in an X11 DESKTOP-type window. Click-through enabled.
"""

import os, sys, signal, gi

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
    print("Error: WebKit2GTK not found.\n"
          "  Oracle Linux:  sudo dnf install webkit2gtk3\n"
          "  Ubuntu/Debian: sudo apt install gir1.2-webkit2-4.1",
          file=sys.stderr)
    sys.exit(1)

from gi.repository import Gtk, Gdk, WebKit2, GLib
import cairo

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

def on_realize(win):
    """
    Set an empty input shape on the X11 window so all mouse/keyboard events
    pass through to whatever is underneath (the GNOME desktop / Nautilus).
    Without this, right-clicking the desktop doesn't work because our window
    absorbs every click even though it's visually behind everything.
    """
    gdk_win = win.get_window()
    if gdk_win is None:
        return
    try:
        # Empty Cairo region = zero-area input mask = fully click-through
        empty = cairo.Region()
        gdk_win.input_shape_combine_region(empty, 0, 0)
        print("Click-through enabled (empty input shape set)", flush=True)
    except Exception as e:
        print(f"Warning: could not set click-through: {e}", flush=True)

def main():
    html_path = get_html_path()
    html_uri  = f"file://{html_path}"

    display = Gdk.Display.get_default()
    if display is None:
        print("Error: cannot connect to display.\n"
              "Run from a desktop session, not SSH.", file=sys.stderr)
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

    # Connect realize handler BEFORE show_all so the input shape
    # is set as soon as the X11 window handle exists
    win.connect("realize", on_realize)

    # ── WebKit settings ──────────────────────────────────────────────────────
    webview  = WebKit2.WebView()
    settings = webview.get_settings()

    settings.set_enable_javascript(True)
    settings.set_enable_webgl(True)
    settings.set_enable_write_console_messages_to_stdout(True)

    # ON_DEMAND: use GPU if available, fall back to WebKit's own CPU canvas
    # renderer (not Mesa llvmpipe) when no GPU is present.
    # NEVER: disable GPU compositing entirely — best for servers with no GPU.
    # Change to ALWAYS only if you have a confirmed discrete GPU.
    settings.set_hardware_acceleration_policy(
        WebKit2.HardwareAccelerationPolicy.NEVER
    )

    # Disable features we don't need — each saves memory and CPU
    settings.set_enable_plugins(False)
    settings.set_enable_page_cache(False)
    settings.set_enable_dns_prefetching(False)
    settings.set_enable_xss_auditor(False)

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
