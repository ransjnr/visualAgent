from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess


@dataclass(frozen=True)
class WindowContext:
    platform: str
    active_app: str | None
    active_title: str | None


def _linux_active_window_title() -> tuple[str | None, str | None]:
    """
    Best-effort. Works on X11 with xdotool installed; returns (app, title).
    On Wayland or without xdotool, returns (None, None).
    """
    if os.environ.get("WAYLAND_DISPLAY"):
        return (None, None)
    try:
        wid = subprocess.check_output(["xdotool", "getactivewindow"], text=True).strip()
        title = subprocess.check_output(["xdotool", "getwindowname", wid], text=True).strip()
        # WM_CLASS is a decent proxy for "app"
        wm_class = subprocess.check_output(["xprop", "-id", wid, "WM_CLASS"], text=True).strip()
        return (wm_class, title)
    except Exception:
        return (None, None)


def get_window_context() -> WindowContext:
    plat = os.uname().sysname.lower()
    if plat == "linux":
        app, title = _linux_active_window_title()
        return WindowContext(platform="linux", active_app=app, active_title=title)
    return WindowContext(platform=plat, active_app=None, active_title=None)

