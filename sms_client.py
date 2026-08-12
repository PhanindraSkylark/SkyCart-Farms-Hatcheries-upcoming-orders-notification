"""MSG91 Flow SMS client (same auth key / API as AppBackend.sms)."""

from __future__ import annotations

from typing import Iterable

import requests

import config


def normalize_phone_10(raw: str | None) -> str | None:
    if not raw:
        return None
    phone = str(raw).strip()[-10:]
    if phone.isdigit() and len(phone) == 10:
        return phone
    return None


def send_delivery_reminder_sms(
    *,
    customer_name: str,
    delivery_date: str,
    phones: Iterable[str],
) -> bool:
    """
    Template 6a7afa86b20355506f0bea73 (MSG91 Flow, 2 vars):
      Chicks delivery scheduled for ##var1## on ##var2##. Please plan the dispatch. -SKLRHT
      var1 = customer / company name
      var2 = requested delivery date (YYYY-MM-DD)
    """
    template_id = config.MSG91_DELIVERY_REMINDER_TEMPLATE_ID.strip()
    var1 = (customer_name or "").strip()
    var2 = (delivery_date or "").strip()
    if not var1 or not var2:
        print("[sms] Skipping - missing customer name or delivery date", flush=True)
        return False

    seen: set[str] = set()
    recipients: list[dict] = []
    for raw in phones:
        phone = normalize_phone_10(raw)
        if not phone or phone in seen:
            continue
        recipients.append(
            {
                "mobiles": f"91{phone}",
                "var1": var1,
                "var2": var2,
            }
        )
        seen.add(phone)

    if not recipients:
        print("[sms] No valid supervisor numbers - SMS not sent", flush=True)
        return False

    if config.is_dry_run():
        print(
            f"[DRY_RUN] Would SMS {len(recipients)} number(s) "
            f"(template={template_id or 'PENDING'}): "
            f"var1={var1!r} var2={var2!r} phones={[r['mobiles'] for r in recipients]}",
            flush=True,
        )
        return True

    if not template_id:
        raise RuntimeError(
            "MSG91_DELIVERY_REMINDER_TEMPLATE_ID is empty in config.py."
        )

    print(
        f"[sms] Sending MSG91 flow {template_id} to {len(recipients)} recipient(s)...",
        flush=True,
    )
    response = requests.post(
        "https://api.msg91.com/api/v5/flow",
        json={
            "template_id": template_id,
            "short_url": "0",
            "recipients": recipients,
            "sender": config.MSG91_SENDER_ID,
        },
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "authkey": config.MSG91_AUTH_KEY,
        },
        timeout=30,
    )
    data = response.json() if response.content else {}
    print(f"[sms] Delivery reminder response -> {data}", flush=True)
    return response.status_code == 200 and data.get("type") == "success"
