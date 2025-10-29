# app/utils.py
import os
from datetime import datetime
from flask import current_app
from flask import request, url_for
from math import ceil

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

#   Convert a datetime value into a short, human-readable relative time string.
#   "Just now" for dates less than 1 minute ago
def time_ago(dt: datetime | None) -> str:
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

 # Format a datetime as "Sep 25, 2025 9:00am" for card display
def card_datetime(dt: datetime | None) -> str:
    if not dt:
        return ""
    hour12 = dt.strftime("%I").lstrip("0") or "0"
    return f"{MONTH_ABBR[dt.month-1]} {dt.day}, {dt.year} {hour12}:{dt.strftime('%M')}{dt.strftime('%p').lower()}"

## Returns a date string in DD-MM-YYYY format
def table_date(dt: datetime | None) -> str:     # "23-09-2025"
    if not dt:
        return ""
    return dt.strftime("%d-%m-%Y")

#Parse a date and time string into a naive datetime object.
#parse_dt("2025-09-23", "09:30")        # → datetime(2025, 9, 23, 9, 30)
def parse_dt(date_str: str | None, time_str: str | None) -> datetime | None:
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
    This function combines a date string (like "2025-10-28") and a time string ("09", "45", "AM")
into a single Python datetime object, which represents a complete date and time together.
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
ALLOWED_ROLES = {"principal", "hod", "faculty", "admin", "other"}
#This function takes an input string raw (like a role name from a form or API),
#cleans it up (trims spaces, converts to lowercase),
def clean_role(raw: str | None) -> str | None:
    role = (raw or "").strip().lower()
    return role if role in ALLOWED_ROLES else None

#This function cleans, validates, and normalizes a phone number string.
def clean_phone(raw: str | None) -> str | None:
    """Keep digits, + and spaces; enforce simple length 7–15 on digits."""
    if not raw:
        return None
    s = "".join(ch for ch in raw if ch.isdigit() or ch in "+ ")
    digits = [c for c in s if c.isdigit()]
    if len(digits) < 7 or len(digits) > 15:
        return None
    return s.strip() or None

#FUNCTIONS FOR APIS
# ---------- API Request Helpers ----------

def normalize_keys(d: dict) -> dict:
    """Normalize input keys: lowercases, replaces spaces/hyphens with underscores."""
    out = {}
    for k, v in (d or {}).items():
        kk = str(k).strip().lower().replace("-", "_").replace(" ", "_")
        out[kk] = v
    return out


def get_scalar(request, data: dict, key: str, default=None):
    """Fetch a single scalar value (works for JSON or form-data)."""
    if request.is_json:
        return data.get(key, default)
    vals = data.get(key)
    if vals is None:
        return default
    return vals[0] if isinstance(vals, list) and vals else default

#“get a list of values regardless of how the client sent them (JSON array, repeated form fields, or comma-separated string)
def get_list(request, data: dict, key: str) -> list:
    """Fetch a list of values (works for JSON, repeated form keys, or comma lists)."""
    if request.is_json:
        val = data.get(key)
        if val is None:
            return []
        return val if isinstance(val, list) else [val]

    vals = data.get(key) or data.get(f"{key}[]") or []
    if not isinstance(vals, list):
        vals = [vals]

    expanded = []
    for item in vals:
        if isinstance(item, str) and "," in item:
            expanded.extend([x.strip() for x in item.split(",") if x.strip()])
        else:
            expanded.append(item)
    return expanded

def _to_bool(v):
    """Safely interpret truthy values from JSON or form fields."""
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "on"}
