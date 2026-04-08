#!/usr/bin/env python3
"""
html-wallpaper.py — Render an HTML file as a live GNOME desktop wallpaper.

Uses WebKit2GTK in an X11 window with _NET_WM_WINDOW_TYPE_DESKTOP,
which GNOME Shell pins below all other windows (works on both X11 and
Wayland+XWayland sessions).
"""

import os
import sys
import signal
import gi

# Force X11 backend so we can set X11 window properties even on Wayland.
# On a pure X11 session this is harmless (already X11).
# On Wayland, this makes our window go through XWayland, where GNOME Shell
# still respects _NET_WM_WINDOW_TYPE_DESKTOP and pins us below everything.
os.environ["GDK_BACKEND"] = "x11"

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

# Auto-detect WebKit2 version: Oracle Linux 9 ships 4.0, Ubuntu 24 ships 4.1
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


def main():
    html_path = get_html_path()
    html_uri = f"file://{html_path}"

    display = Gdk.Display.get_default()
    if display is None:
        print("Error: cannot connect to display. Make sure DISPLAY is set.\n"
              "This script must run inside a desktop session (autostart),\n"
              "not from SSH or a systemd service.", file=sys.stderr)
        sys.exit(1)

    monitor = display.get_primary_monitor() or display.get_monitor(0)
    geom = monitor.get_geometry()
    scale = monitor.get_scale_factor()
    print(f"Screen: {geom.width}x{geom.height} scale={scale}", flush=True)

    # --- window setup ---
    win = Gtk.Window(title="html-wallpaper")
    win.set_decorated(False)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.set_accept_focus(False)
    win.set_default_size(geom.width, geom.height)
    win.move(geom.x, geom.y)

    # THE KEY LINE: tells GNOME Shell "I am the desktop background"
    win.set_type_hint(Gdk.WindowTypeHint.DESKTOP)

    # --- webview setup ---
    # Use a single process (no network worker, no service workers).
    # This is a local file wallpaper — we don't need multi-process security.
    ctx = WebKit2.WebContext.get_default()
    ctx.set_cache_model(WebKit2.CacheModel.DOCUMENT_VIEWER)

    webview = WebKit2.WebView.new_with_context(ctx)

    settings = webview.get_settings()
    settings.set_enable_javascript(True)
    settings.set_enable_webgl(True)
    settings.set_hardware_acceleration_policy(
        WebKit2.HardwareAccelerationPolicy.ALWAYS
    )
    settings.set_enable_page_cache(False)
    settings.set_enable_write_console_messages_to_stdout(True)
    webview.set_settings(settings)

    webview.set_background_color(Gdk.RGBA(0, 0, 0, 1))

    # Suppress WebKit's right-click context menu (reload/back/forward)
    webview.connect("context-menu", lambda *_: True)

    win.add(webview)
    webview.load_uri(html_uri)
    print(f"Loading: {html_uri}", flush=True)

    # Make the window click-through: set an empty input shape so all mouse
    # events pass to the desktop underneath (right-click menus, icons, etc.)
    def on_realize(widget):
        gdk_win = widget.get_window()
        empty = cairo.Region(cairo.RectangleInt(0, 0, 0, 0))
        gdk_win.input_shape_combine_region(empty, 0, 0)
        print("Input passthrough enabled", flush=True)

    win.connect("realize", on_realize)

    win.connect("destroy", lambda *_: Gtk.main_quit())
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, Gtk.main_quit)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, Gtk.main_quit)

    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
