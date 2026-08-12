"""SQL Server via pymssql + FreeTDS (same approach as Sales Reports Email on Azure VM)."""

from __future__ import annotations

import logging
import socket
import threading
import time

import pymssql

import config

logger = logging.getLogger(__name__)

_local = threading.local()
_CONNECT_MAX_RETRIES = 3
_CONNECT_RETRY_DELAY_SEC = 1


def _log(message: str) -> None:
    print(message, flush=True)
    logger.info(message)


def _tcp_reachable(host: str, port: int, timeout_sec: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except OSError as exc:
        _log(f"[DB] TCP {host}:{port} not reachable ({timeout_sec}s) - {exc}")
        return False


def _connect_pymssql(host: str, port: int):
    return pymssql.connect(
        server=host,
        port=port,
        user=config.MSSQL_USER,
        password=config.MSSQL_PASSWORD,
        database=config.MSSQL_DATABASE,
        login_timeout=config.MSSQL_LOGIN_TIMEOUT,
        timeout=config.MSSQL_QUERY_TIMEOUT,
        autocommit=True,
    )


def get_connection():
    if getattr(_local, "conn", None) is not None:
        try:
            cur = _local.conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return _local.conn
        except (pymssql.Error, AttributeError):
            try:
                _local.conn.close()
            except Exception:
                pass
            _local.conn = None

    port = int(config.MSSQL_PORT or 1433)
    hosts = config.mssql_host_candidates()
    tcp_timeout = config.MSSQL_CONNECT_TIMEOUT

    _log(
        f"[DB] Connecting with pymssql to {config.MSSQL_DATABASE} "
        f"(hosts={hosts}, port={port}, tcp_timeout={tcp_timeout}s)"
    )

    last_error = None
    for host in hosts:
        if not _tcp_reachable(host, port, tcp_timeout):
            last_error = ConnectionError(f"{host}: TCP unreachable")
            continue
        for attempt in range(1, _CONNECT_MAX_RETRIES + 1):
            try:
                _log(f"[DB] pymssql login {host}:{port} (attempt {attempt})...")
                _local.conn = _connect_pymssql(host, port)
                config.MSSQL_CONFIG["server"] = host
                _log(f"[DB] Connected OK via pymssql -> {host}/{config.MSSQL_DATABASE}")
                return _local.conn
            except Exception as exc:
                last_error = exc
                _local.conn = None
                _log(f"[DB] pymssql connect attempt {attempt} failed: {exc}")
                if attempt < _CONNECT_MAX_RETRIES:
                    time.sleep(_CONNECT_RETRY_DELAY_SEC)

    raise last_error if last_error else RuntimeError("SQL Server connection failed")


class production_cursor:
    """Context manager with the same usage as Sales Reports Email mssql_conn."""

    def __enter__(self):
        self._conn = get_connection()
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, *args):
        try:
            self._cursor.close()
        except Exception:
            pass
