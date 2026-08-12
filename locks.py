"""Prevent duplicate daily SMS runs when scheduler misfires or container restarts."""

from __future__ import annotations

import os
import sys
import tempfile

import config

_lock_handles: dict[str, object] = {}


def try_acquire_daily_send_lock(send_date: str) -> bool:
    if config.is_force_send():
        print(f"[lock] FORCE enabled - allowing send for {send_date}", flush=True)
        return True

    if sys.platform == "win32":
        if send_date in _lock_handles:
            return False
        _lock_handles[send_date] = object()
        return True

    import fcntl

    lock_path = os.path.join(
        tempfile.gettempdir(),
        f"skylark_chicks_delivery_sms_{send_date}.lock",
    )
    try:
        handle = open(lock_path, "w", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        handle.write(str(os.getpid()))
        handle.flush()
        _lock_handles[send_date] = handle
        return True
    except OSError:
        print(
            f"[lock] Delivery SMS already sent or in progress for {send_date}",
            flush=True,
        )
        return False
