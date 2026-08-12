# Chicks Delivery Date Notification

## What this does

This is a **standalone Docker worker** that reminds hatch supervisors about upcoming chick deliveries.

Every day at **09:40 IST** it:

1. Connects to Production SQL Server with **pymssql** (same stack as Sales Reports Email on the Azure VM)
2. Finds **priced** orders from **Hatcheries** and **Farms** whose **Requested Delivery Date** is between **today** and **today + 14 days**
3. Sends one MSG91 SMS per order to the hatch supervisor numbers configured in `config.py`

**SMS template**

```
Chicks delivery scheduled for ##var1## on ##var2##. Please plan the dispatch. -SKLRHT
```

| Field | Meaning |
|-------|---------|
| Template id | `6a7afa86b20355506f0bea73` |
| `var1` | Customer / company name |
| `var2` | Requested delivery date (`YYYY-MM-DD`) |

## Config

- **Required at runtime:** only `MSSQL_*` database credentials (`.env` or `-e`)
- **Predefined in code:** schedule, SMS template/settings, supervisor numbers, delivery window

Example `.env`:

```env
MSSQL_SERVER
MSSQL_PORT
MSSQL_DATABASE
MSSQL_USER
MSSQL_PASSWORD
```
