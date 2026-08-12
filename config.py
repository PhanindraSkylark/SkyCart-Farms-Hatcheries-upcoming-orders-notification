"""
Runtime config for Chicks Delivery Date Notification.

Only database credentials come from .env / environment.
Everything else is predefined (same stack as Sales Reports Email on the Azure VM).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env(key: str, default: str | None = None) -> str | None:
    value = os.getenv(key, default)
    if value is None:
        return default
    value = str(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return value


def _require(key: str) -> str:
    value = _env(key)
    if not value:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


# ---------------------------------------------------------------------------
# Database credentials only (from .env / -e) — MSSQL_* only
# ---------------------------------------------------------------------------
MSSQL_SERVER = _require("MSSQL_SERVER")
MSSQL_PORT = _env("MSSQL_PORT") or "1433"
MSSQL_DATABASE = _require("MSSQL_DATABASE")
MSSQL_USER = _require("MSSQL_USER")
MSSQL_PASSWORD = _require("MSSQL_PASSWORD")
MSSQL_FALLBACK_SERVERS = _env("MSSQL_FALLBACK_SERVERS") or ""

# Connection timeouts (predefined)
MSSQL_CONNECT_TIMEOUT = 5
MSSQL_LOGIN_TIMEOUT = 8
MSSQL_QUERY_TIMEOUT = 60


def mssql_host_candidates() -> list[str]:
    hosts: list[str] = []
    for host in [MSSQL_SERVER, *[h.strip() for h in MSSQL_FALLBACK_SERVERS.split(",")]]:
        if host and host not in hosts:
            hosts.append(host)
    return hosts


MSSQL_CONFIG = {
    "server": MSSQL_SERVER,
    "port": MSSQL_PORT,
    "database": MSSQL_DATABASE,
    "user": MSSQL_USER,
    "password": MSSQL_PASSWORD,
}

# ---------------------------------------------------------------------------
# Predefined — not read from .env
# ---------------------------------------------------------------------------

# Same hatch supervisor mobiles as AppBackend.login.MANUAL_HATCH_SUPERVISOR_NUMBERS
HATCH_SUPERVISOR_NUMBERS = {
    "9121147244","7338853763","9978996929","9813609911", "9310628653",
}

# MSG91 (AppBackend settings / sms.py)
MSG91_AUTH_KEY = _env("MSG91_AUTH_KEY")
MSG91_SENDER_ID = _env("MSG91_SENDER_ID")
# Chicks delivery scheduled for ##var1## on ##var2##. Please plan the dispatch. -SKLRHT
MSG91_DELIVERY_REMINDER_TEMPLATE_ID =  _env("MSG91_DELIVERY_REMINDER_TEMPLATE_ID")

DELIVERY_WINDOW_DAYS = 14
SCHEDULE_HOUR = 9
SCHEDULE_MINUTE = 40
TIMEZONE = "Asia/Kolkata"
DRY_RUN = False
SCHEDULER_ENABLED = True
FORCE_SEND = False

HATCHERIES_API_ORDER_TABLE = "[dbo].[Skylark Hatcheries Pvt_ Ltd_$Api_order]"
HATCHERIES_API_ORDERITEM_TABLE = "[dbo].[Skylark Hatcheries Pvt_ Ltd_$Api_orderitem]"
FARMS_API_ORDER_TABLE = "[dbo].[Skylark Farms$Api_order]"
FARMS_API_ORDERITEM_TABLE = "[dbo].[Skylark Farms$Api_orderitem]"


def is_dry_run() -> bool:
    return DRY_RUN


def is_force_send() -> bool:
    return FORCE_SEND
