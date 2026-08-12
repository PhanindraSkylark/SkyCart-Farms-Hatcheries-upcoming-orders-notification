"""
APScheduler for chicks delivery SMS — same pattern as Sales Reports Email.

Fires daily at 09:40 IST. Use scripts/delivery_worker.py in Docker on the VM.
"""

from __future__ import annotations

import os
import sys
import tempfile

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from job import run_delivery_reminders

IST_TZ = "Asia/Kolkata"
_scheduler = None
_scheduler_lock_handle = None


def _log(message: str) -> None:
    print(f"[Skylark] {message}", flush=True)


def _schedule_label() -> str:
    return f"{config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d} IST ({IST_TZ})"


def _try_acquire_scheduler_lock() -> bool:
    """Ensure only one process per host runs the scheduler (Linux VM / Docker)."""
    global _scheduler_lock_handle

    if sys.platform == "win32":
        return True

    import fcntl

    lock_path = os.path.join(
        tempfile.gettempdir(),
        "skylark_chicks_delivery_sms_scheduler.lock",
    )
    try:
        handle = open(lock_path, "w", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        handle.write(str(os.getpid()))
        handle.flush()
        _scheduler_lock_handle = handle
        return True
    except OSError:
        _log(f"Delivery SMS scheduler skipped - another process owns {lock_path}")
        return False


def _run_scheduled_job() -> None:
    _log(f"Running scheduled delivery SMS ({_schedule_label()})...")
    try:
        result = run_delivery_reminders()
        if result.get("skipped"):
            _log(
                f"Delivery SMS skipped - {result.get('reason', 'already_sent')} "
                f"for {result.get('as_of', '')}"
            )
            return
        _log(
            f"Delivery SMS OK - orders={result.get('orders', 0)} "
            f"sent={result.get('sent', 0)} failed={result.get('failed', 0)} "
            f"dry_run={result.get('dry_run')}"
        )
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Scheduled delivery SMS failed")
        _log("Scheduled delivery SMS FAILED - see logs")


def start_delivery_sms_scheduler() -> None:
    global _scheduler

    if not config.SCHEDULER_ENABLED:
        _log("Delivery SMS scheduler disabled (SCHEDULER_ENABLED=false in config.py)")
        return

    if not _try_acquire_scheduler_lock():
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(timezone=IST_TZ)
    job = _scheduler.add_job(
        _run_scheduled_job,
        trigger=CronTrigger(
            hour=config.SCHEDULE_HOUR,
            minute=config.SCHEDULE_MINUTE,
            second=0,
            timezone=IST_TZ,
        ),
        id="chicks_delivery_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()

    next_run = job.next_run_time
    next_run_label = (
        next_run.strftime("%Y-%m-%d %H:%M:%S %Z")
        if next_run is not None
        else _schedule_label()
    )
    _log(
        f"Delivery SMS scheduler started - fires daily at {_schedule_label()}; "
        f"next run {next_run_label}; dry_run={config.DRY_RUN}"
    )


if __name__ == "__main__":
    import time

    start_delivery_sms_scheduler()
    while True:
        time.sleep(3600)
