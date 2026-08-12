"""Daily job: priced orders due in next N days → SMS hatch supervisors."""

from __future__ import annotations

from datetime import date

import config
from locks import try_acquire_daily_send_lock
from orders import fetch_priced_delivery_orders
from sms_client import send_delivery_reminder_sms


def run_delivery_reminders(*, as_of: date | None = None) -> dict:
    today = as_of or date.today()
    as_of_label = today.isoformat()
    dry_run = config.is_dry_run()
    phones = sorted(config.HATCH_SUPERVISOR_NUMBERS)

    print(
        f"[job] Delivery reminders starting | as_of={as_of_label} "
        f"| window={config.DELIVERY_WINDOW_DAYS} days | dry_run={dry_run}",
        flush=True,
    )
    print(
        f"[job] Template={config.MSG91_DELIVERY_REMINDER_TEMPLATE_ID} "
        f"| recipients={phones}",
        flush=True,
    )
    print(
        f"[job] SQL hosts={config.mssql_host_candidates()} "
        f"db={config.MSSQL_DATABASE}",
        flush=True,
    )

    if not try_acquire_daily_send_lock(as_of_label):
        print(
            f"[job] Skipped - already sent or in progress for {as_of_label} "
            f"(use: python run_once.py --force to override)",
            flush=True,
        )
        return {
            "as_of": as_of_label,
            "skipped": True,
            "reason": "already_sent_or_in_progress",
            "dry_run": dry_run,
        }

    try:
        print("[job] Fetching priced orders from Production...", flush=True)
        orders = fetch_priced_delivery_orders(as_of=today)
    except Exception as exc:
        print(f"[job] FAILED while loading orders: {exc}", flush=True)
        raise

    sent = 0
    failed = 0
    skipped = 0

    if not orders:
        print("[job] No priced orders with delivery in the reminder window.", flush=True)
        return {
            "as_of": as_of_label,
            "orders": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "dry_run": dry_run,
        }

    print(f"[job] Found {len(orders)} priced order(s) to notify.", flush=True)

    for index, order in enumerate(orders, start=1):
        delivery = order.requested_delivery_date.isoformat()
        print(
            f"[job] ({index}/{len(orders)}) [{order.segment}] order={order.order_id} "
            f"customer={order.customer_name!r} date={delivery}",
            flush=True,
        )
        try:
            ok = send_delivery_reminder_sms(
                customer_name=order.customer_name,
                delivery_date=delivery,
                phones=phones,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[error] SMS failed for order {order.order_id}: {exc}", flush=True)
            failed += 1
            continue

        if ok:
            sent += 1
        else:
            skipped += 1

    summary = {
        "as_of": as_of_label,
        "orders": len(orders),
        "sent": sent,
        "failed": failed,
        "skipped": skipped,
        "dry_run": dry_run,
        "recipients": phones,
    }
    print(f"[job] Done: {summary}", flush=True)
    return summary
