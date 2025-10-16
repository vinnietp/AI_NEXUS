# app/utils.py
import os
from datetime import datetime
from flask import current_app

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def time_ago(dt: datetime | None) -> str:
    """Convert a datetime to a human-readable relative time (naive -> local)."""
    if not dt:
        return ""
    now = datetime.now(tz=dt.tzinfo) if getattr(dt, "tzinfo", None) else datetime.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = seconds // 86400
    return f"{days} day{'s' if days != 1 else ''} ago"


def card_datetime(dt: datetime | None) -> str:  # "Sep 25, 2025 9:00am"
    if not dt:
        return ""
    hour12 = dt.strftime("%I").lstrip("0") or "0"
    return f"{MONTH_ABBR[dt.month-1]} {dt.day}, {dt.year} {hour12}:{dt.strftime('%M')}{dt.strftime('%p').lower()}"


def table_date(dt: datetime | None) -> str:     # "23-09-2025"
    if not dt:
        return ""
    return dt.strftime("%d-%m-%Y")


def parse_dt(date_str: str | None, time_str: str | None) -> datetime | None:
    """
    Parse 'YYYY-MM-DD' + 'HH:MM' (24h). Returns naive datetime (treated as local/IST in your app).
    Falls back to 'YYYY-MM-DD HH:MM AM/PM'.
    """
    if not date_str or not time_str:
        return None
    s = f"{date_str.strip()} {time_str.strip()}"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ---------- Moved from routes.py ----------
def hm_ampm_to_24(hour_str: str, minute_str: str, ampm: str) -> tuple[int, int]:
    """Convert 12h + AM/PM to 24h hour, minute."""
    h = int(hour_str)
    m = int(minute_str)
    ampm = (ampm or "").upper()
    if ampm == "PM" and h != 12:
        h += 12
    if ampm == "AM" and h == 12:
        h = 0
    return h, m


def local_date_hm_ampm_to_naive(date_str: str, hour_str: str, minute_str: str, ampm: str) -> datetime:
    """
    Combine YYYY-MM-DD + 12h HH/MM/AMPM into a naive datetime.
    Treated as local IST elsewhere in the app.
    """
    y, mo, d = [int(x) for x in (date_str or "").split("-")]  # "YYYY-MM-DD"
    hh, mm = hm_ampm_to_24(hour_str, minute_str, ampm)
    return datetime(y, mo, d, hh, mm)


def relpath_from_static(abs_path: str) -> str:
    """
    Return path relative to app.static_folder for url_for('static', filename=...).
    Requires an active app/request context.
    """
    return os.path.relpath(abs_path, start=current_app.static_folder).replace("\\", "/")


# ---------- Validation helpers (moved) ----------
# ---------- Validation helpers (moved) ----------
ALLOWED_ROLES = {"principal", "hod", "faculty", "admin", "other"}

def clean_role(raw: str | None) -> str | None:
    role = (raw or "").strip().lower()
    return role if role in ALLOWED_ROLES else None

def clean_phone(raw: str | None) -> str | None:
    """Keep digits, + and spaces; enforce simple length 7–15 on digits."""
    if not raw:
        return None
    s = "".join(ch for ch in raw if ch.isdigit() or ch in "+ ")
    digits = [c for c in s if c.isdigit()]
    if len(digits) < 7 or len(digits) > 15:
        return None
    return s.strip() or None
