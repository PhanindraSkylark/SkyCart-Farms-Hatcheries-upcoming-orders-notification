"""Fetch priced chicks orders due within the delivery reminder window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal

import config
from db import fetchall

Segment = Literal["hatcheries", "farms"]


@dataclass(frozen=True)
class DeliveryReminderOrder:
    order_id: int
    segment: Segment
    customer_name: str
    requested_delivery_date: date


def _as_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    return datetime.strptime(text[:10], "%Y-%m-%d").date()


def _priced_orders_sql(order_table: str, orderitem_table: str) -> str:
    # Same priced definition as hatcheries_supervisor / farm_supervisor priced endpoints.
    # pymssql placeholders are %s (same as Sales Reports Email).
    return f"""
        SELECT DISTINCT
            o.[id] AS order_id,
            o.[Customer Name] AS customer_name,
            CAST(o.[Requested Delivery Date] AS DATE) AS requested_delivery_date
        FROM {order_table} o
        WHERE CAST(o.[Requested Delivery Date] AS DATE) >= %s
          AND CAST(o.[Requested Delivery Date] AS DATE) <= %s
          AND EXISTS (
              SELECT 1
              FROM {orderitem_table} oi
              WHERE oi.[order_id] = o.[id]
                AND NOT (
                    oi.[cost] = 1
                    AND oi.[discounted_cost] IS NULL
                )
          )
        ORDER BY requested_delivery_date ASC, order_id ASC
    """


def fetch_priced_delivery_orders(
    *,
    window_days: int | None = None,
    as_of: date | None = None,
) -> list[DeliveryReminderOrder]:
    today = as_of or date.today()
    days = config.DELIVERY_WINDOW_DAYS if window_days is None else window_days
    end = today + timedelta(days=days)

    print(
        f"[orders] Loading priced orders | {today.isoformat()} -> {end.isoformat()} "
        f"({days} days)",
        flush=True,
    )

    sources: list[tuple[Segment, str, str]] = [
        (
            "hatcheries",
            config.HATCHERIES_API_ORDER_TABLE,
            config.HATCHERIES_API_ORDERITEM_TABLE,
        ),
        (
            "farms",
            config.FARMS_API_ORDER_TABLE,
            config.FARMS_API_ORDERITEM_TABLE,
        ),
    ]

    orders: list[DeliveryReminderOrder] = []
    for segment, order_table, orderitem_table in sources:
        print(f"[orders] Querying {segment}...", flush=True)
        try:
            rows = fetchall(
                _priced_orders_sql(order_table, orderitem_table),
                [today.isoformat(), end.isoformat()],
            )
        except Exception as exc:
            print(f"[orders] {segment} query FAILED: {exc}", flush=True)
            raise
        print(f"[orders] {segment}: {len(rows)} row(s)", flush=True)

        for order_id, customer_name, requested_delivery_date in rows:
            delivery_date = _as_date(requested_delivery_date)
            name = (customer_name or "").strip()
            if not delivery_date or not name:
                continue
            orders.append(
                DeliveryReminderOrder(
                    order_id=int(order_id),
                    segment=segment,
                    customer_name=name,
                    requested_delivery_date=delivery_date,
                )
            )

    orders.sort(key=lambda o: (o.requested_delivery_date, o.segment, o.order_id))
    print(f"[orders] Total priced orders in window: {len(orders)}", flush=True)
    return orders
