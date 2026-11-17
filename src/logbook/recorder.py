# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
"""Ask Windows which window is in front, every few seconds, and store what the settings allow."""

from __future__ import annotations

import time
from pathlib import Path

from .settings import Settings
from .store import Store

PRUNE_EVERY = 720  # samples; about hourly at the default interval


def foreground() -> tuple[str, str] | None:
    """(executable name in lower case, window title) of the window in front, or None (lock screen, no window)."""
    import ctypes
    from ctypes import wintypes

    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    # handles are pointer-sized; without these declarations ctypes cuts them to 32 bits
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    window = user32.GetForegroundWindow()
    if not window:
        return None
    title = ctypes.create_unicode_buffer(512)
    user32.GetWindowTextW(window, title, 512)
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(window, ctypes.byref(pid))

    app = "unknown"  # protected processes cannot be opened; they are still counted, under this name
    process = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if process:
        path, size = ctypes.create_unicode_buffer(1024), wintypes.DWORD(1024)
        if kernel32.QueryFullProcessImageNameW(process, 0, path, ctypes.byref(size)):
            app = Path(path.value).name.lower()
        kernel32.CloseHandle(process)
    return app, title.value


def sample(settings: Settings, store: Store, now: float, window: tuple[str, str] | None) -> None:
    if window is None or settings.pause_file.exists():
        return
    app, title = window
    if app in settings.exclude_apps:
        return
    stored_title = title if app in settings.title_apps else ""  # titles leak document and email names
    store.add(app, stored_title, now, max_gap=3 * settings.interval_seconds)


def record(settings: Settings, store: Store) -> None:
    """Run until interrupted."""
    count = 0
    while True:
        now = time.time()
        if count % PRUNE_EVERY == 0:
            store.prune(now - settings.retention_days * 86400)
        sample(settings, store, now, foreground())
        count += 1
        time.sleep(settings.interval_seconds)
