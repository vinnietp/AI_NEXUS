from __future__ import annotations
from datetime import datetime
from uuid import uuid4
from math import ceil
import os
from typing import Any

from flask import Blueprint, jsonify, request, url_for, current_app
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
from werkzeug.utils import secure_filename

from models import (
    db,
    Club,
    Event,
    Coordinator,
    College,
    Member,
    Announcement,
    member_clubs,
)
from utils import (
    normalize_keys,
    get_scalar,
    get_list,
    time_ago,
    clean_role,
    clean_phone,
    parse_dt, _to_bool,
)

# =====================================================================
# Blueprint
# =====================================================================
api = Blueprint("api", __name__, url_prefix="/api")

# =====================================================================
# Constants
# =====================================================================
EVENT_STATUS_VALUES = {"upcoming", "completed", "cancelled"}
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

# =====================================================================
# Response helpers (kept compatible with your old UI)
# =====================================================================
def ok(data: Any = None, status: int = 200, **meta):
    payload = {"status": True, "data": data}
    if meta:
        payload["meta"] = meta
    return jsonify(payload), status


def err(message: str, status: int = 400, code: str = "bad_request"):
    return jsonify({"status": False, "error": {"code": code, "message": message}}), status


# =====================================================================
# Query helpers (your old _qstr/_qint are preserved and used)
# =====================================================================

def _qstr(name: str, default: str = "") -> str:
    return (request.args.get(name) or default).strip()


def _qint(name: str, default: int | None = None) -> int | None:
    return request.args.get(name, default, type=int)


# =====================================================================
# Generic helpers
# =====================================================================

def image_url(relpath: str | None):
    if not relpath:
        return None
    return url_for("static", filename=relpath, _external=True)


def _parse_bool(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "on"}


def _iso_to_naive(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _coerce_int(val):
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _payload():
    js = request.get_json(silent=True) or {}
    fm = request.form.to_dict(flat=False) if request.form else {}
    va = request.values.to_dict(flat=False)
    raw = js or fm or va
    return normalize_keys(raw)


def _paginate(query, page_default=1, per_default=20, per_max=100):
    page = max(1, request.args.get("page", page_default, type=int) or page_default)
    per_page = min(per_max, request.args.get("per_page", per_default, type=int) or per_default)
    total = query.count()
    rows = query.limit(per_page).offset((page - 1) * per_page).all()
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": ceil(total / per_page) if per_page else 1,
    }
    return rows, meta


def _save_upload(file, subdir_key: str):
    if not file or not getattr(file, "filename", ""):
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return None
    base = secure_filename(file.filename.rsplit(".", 1)[0])[:60] or "upload"
    unique = f"{base}-{uuid4().hex[:10]}.{ext}"
    save_dir = current_app.config[subdir_key]
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, unique)
    file.save(save_path)
    return os.path.relpath(save_path, start=current_app.static_folder).replace("\\", "/")


# =====================================================================
# Dashboard (soft-delete aware)
# =====================================================================
@api.get("/dashboard")
def api_dashboard():
    now_local = datetime.now()

    # Recent clubs (latest 2, not deleted)
    clubs = (
        Club.query.filter(Club.is_deleted.is_(False))
        .order_by(Club.club_id.desc())
        .limit(2)
        .all()
    )
    recent_clubs = [{"name": c.club_name, "time_ago": time_ago(c.created_time)} for c in clubs]

    # Card counts (active + not deleted)
    active_clubs = db.session.query(func.count(Club.club_id)).filter(Club.status == "active", Club.is_deleted.is_(False)).scalar() or 0
    active_colleges = db.session.query(func.count(College.college_id)).filter(College.status == "active", College.is_deleted.is_(False)).scalar() or 0
    active_coordinators = db.session.query(func.count(Coordinator.coordinator_id)).filter(Coordinator.status == "active", Coordinator.is_deleted.is_(False)).scalar() or 0
    active_members = db.session.query(func.count(Member.member_id)).filter((Member.status == "active") | (Member.status.is_(None)), Member.is_deleted.is_(False)).scalar() or 0
    total_members = db.session.query(func.count(Member.member_id)).filter(Member.is_deleted.is_(False)).scalar() or 0
    upcoming_events_count = db.session.query(func.count(Event.event_id)).filter(Event.status == "upcoming", Event.is_deleted.is_(False)).scalar() or 0

    # Upcoming (nearest 2)
    upcoming_events_rows = (
        Event.query.filter(Event.is_deleted.is_(False), Event.status != "cancelled", Event.start_at >= now_local)
        .order_by(Event.start_at.asc())
        .limit(2)
        .all()
    )
    upcoming_events = [
        {
            "name": ev.event_name,
            "time_until": time_ago(ev.start_at),
            "description": ev.description or "",
            "start_at": ev.start_at.isoformat() if ev.start_at else None,
        }
        for ev in upcoming_events_rows
    ]

    # Recent events (latest 2)
    recent_events_rows = (
        Event.query.filter(Event.is_deleted.is_(False))
        .order_by(Event.created_time.desc())
        .limit(2)
        .all()
    )
    recent_events = [{"name": ev.event_name, "time_ago": time_ago(ev.created_time)} for ev in recent_events_rows]

    return ok(
        {
            "cards": {
                "active_clubs": active_clubs,
                "active_colleges": active_colleges,
                "active_coordinators": active_coordinators,
                "active_members": active_members,
                "total_members": total_members,
                "upcoming_events": upcoming_events_count,
            },
            "recent_clubs": recent_clubs,
            "upcoming_events": upcoming_events,
            "recent_events": recent_events,
        }
    )


# =====================================================================
# Clubs (GET/POST/PUT/DELETE/RESTORE)
# =====================================================================
@api.get("/clubs")
def api_list_clubs():
    q = _qstr("q")
    status = _qstr("status", "all")  # active|inactive|all
    category = _qstr("category")
    sort = _qstr("sort", "newest")

    # members_count subquery (not counting deleted members)
    member_count_sq = (
        select(func.count(member_clubs.c.member_id))
        .select_from(member_clubs.join(Member, Member.member_id == member_clubs.c.member_id))
        .where(member_clubs.c.club_id == Club.club_id, Member.is_deleted.is_(False))
        .correlate(Club)
        .scalar_subquery()
    )

    query = (
        db.session.query(Club, member_count_sq.label("members_count"))
        .filter(Club.is_deleted.is_(False))
    )

    if q:
        query = query.filter(Club.club_name.ilike(f"%{q}%"))
    if status in ("active", "inactive"):
        query = query.filter(Club.status == status)
    if category:
        query = query.filter(Club.club_category == category)

    if sort == "name":
        query = query.order_by(Club.club_name.asc())
    elif sort == "oldest":
        query = query.order_by(Club.created_time.asc(), Club.club_id.asc())
    else:
        query = query.order_by(Club.created_time.desc(), Club.club_id.desc())

    rows, meta = _paginate(query)

    data = [
        {
            "club_id": c.club_id,
            "club_name": c.club_name,
            "club_category": c.club_category,
            "club_logo": image_url(c.club_logo),
            "description": c.description,
            "status": c.status,
            "created_time": c.created_time.isoformat() if c.created_time else None,
            "members": mc,
        }
        for c, mc in rows
    ]

    return ok(data, **meta)

@api.post("/clubs")
def api_create_club():
    data = _payload()

    # ---- Required: club_name ----
    club_name = (get_scalar(request, data, "club_name") or "").strip()
    if not club_name:
        return err("club_name is required.", 422, "validation_error")

    # ---- Duplicate name check (case-insensitive, only among non-deleted) ----
    existing = (
        db.session.query(Club)
        .filter(
            func.lower(Club.club_name) == club_name.lower(),
            Club.is_deleted.is_(False)
        )
        .first()
    )
    if existing:
        return err("A club with this name already exists.", 409, "duplicate_error")

    # ---- Create club record ----
    club = Club(
        club_name=club_name,
        club_category=(get_scalar(request, data, "club_category") or "").strip() or None,
        description=(get_scalar(request, data, "description") or "").strip() or None,
        status=(get_scalar(request, data, "status") or "active").strip().lower() or "active",
    )

    # ---- Optional: logo upload ----
    file = request.files.get("club_logo")
    if file and file.filename:
        rel = _save_upload(file, "CLUB_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid club_logo format.", 415, "unsupported_media")
        club.club_logo = rel

    # ---- Commit to database ----
    try:
        db.session.add(club)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create club")
        return err("Failed to create club.", 500, "db_error")

    # ---- Success response ----
    return ok({
        "id": club.club_id,
        "club_name": club.club_name,
        "club_category": club.club_category,
        "description": club.description,
        "status": club.status,
    }, 201)

##########################
@api.put("/clubs/<int:club_id>")
def api_update_club(club_id):
    # ---- Fetch the club ----
    club = db.session.get(Club, club_id)
    if not club or club.is_deleted:
        return err("Club not found or deleted.", 404, "not_found")

    # ---- Read payload (works for JSON or form-data) ----
    data = _payload()

    # ---- Validate and update name ----
    name = (get_scalar(request, data, "club_name") or "").strip()
    if name:
        exists = (
            db.session.query(Club)
            .filter(
                Club.is_deleted.is_(False),
                func.lower(Club.club_name) == name.lower(),
                Club.club_id != club_id
            )
            .first()
        )
        if exists:
            return err("Another club with this name exists.", 409, "duplicate")
        club.club_name = name

    # ---- Update optional fields ----
    club.club_category = (
        (get_scalar(request, data, "club_category") or "").strip() or club.club_category
    )
    club.description = (
        (get_scalar(request, data, "description") or "").strip() or club.description
    )

    # ---- Update status (only active/inactive allowed) ----
    status = (get_scalar(request, data, "status") or "").strip().lower()
    if status in {"active", "inactive"}:
        club.status = status

    # ---- Handle logo upload ----
    file = request.files.get("club_logo")
    if file and file.filename:
        rel = _save_upload(file, "CLUB_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid club_logo format.", 415, "unsupported_media")
        club.club_logo = rel

    # ---- Commit changes ----
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update club")
        return err("Failed to update club.", 500, "db_error")

    # ---- Return full updated club data ----
    return ok({
        "club_id": club.club_id,
        "club_name": club.club_name,
        "club_category": club.club_category,
        "description": club.description,
        "status": club.status,
        "club_logo": image_url(club.club_logo),
        "created_time": club.created_time.isoformat() if club.created_time else None,
        "updated_time": getattr(club, "updated_time", None).isoformat()
            if getattr(club, "updated_time", None) else None
    })


@api.delete("/clubs/<int:club_id>")
def api_delete_club(club_id):
    club = db.session.get(Club, club_id)
    if not club:
        return err("Club not found.", 404, "not_found")
    club.is_deleted = True
    club.deleted_at = func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to delete club.", 500, "db_error")
    return ok({
        "id": club.club_id,
        "message": "Club deleted successfully."
    })


# =====================================================================
# Events (GET/POST/PUT/DELETE/RESTORE)
# =====================================================================
@api.get("/events")
def api_list_events():
    now_local = datetime.now()

    q = _qstr("q")
    status = _qstr("status")
    club_id = _qint("organising_club_id") or _qint("club_id")
    date_from = _qstr("date_from")
    date_to = _qstr("date_to")
    sort = _qstr("sort", "created_time")
    order = _qstr("order", "desc")

    query = Event.query.filter(Event.is_deleted.is_(False))

    if q:
        query = query.filter(or_(Event.event_name.ilike(f"%{q}%"), Event.description.ilike(f"%{q}%")))
    if status in EVENT_STATUS_VALUES:
        query = query.filter(Event.status == status)
    if club_id:
        query = query.filter(Event.organising_club_id == club_id)

    def _to_dt(s: str | None):
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None

    dt_from = _to_dt(date_from)
    dt_to = _to_dt(date_to)
    if dt_from:
        query = query.filter(Event.start_at >= dt_from)
    if dt_to:
        query = query.filter(Event.start_at <= dt_to)

    sort_col = Event.created_time if sort == "created_time" else Event.start_at
    query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

    all_rows, meta = _paginate(query)

    upcoming_events_rows = (
        Event.query.filter(Event.is_deleted.is_(False), Event.status != "cancelled", Event.start_at >= now_local)
        .order_by(Event.start_at.asc())
        .limit(3)
        .all()
    )
    upcoming_count = (
        db.session.query(Event).filter(Event.is_deleted.is_(False), Event.status != "cancelled", Event.start_at >= now_local).count()
    )
    completed_count = db.session.query(Event).filter(Event.is_deleted.is_(False), Event.status == "completed").count()

    def ser(ev: Event):
        return {
            "event_id": ev.event_id,
            "event_name": ev.event_name,
            "organising_club_id": ev.organising_club_id,
            "event_coordinator": ev.event_coordinator,
            "venue": ev.venue,
            "start_at": ev.start_at.isoformat() if ev.start_at else None,
            "end_at": ev.end_at.isoformat() if ev.end_at else None,
            "event_image": image_url(ev.event_image) if ev.event_image else None,
            "max_participants": ev.max_participants,
            "status": ev.status,
            "description": ev.description or "",
            "created_time": ev.created_time.isoformat() if ev.created_time else None,
        }

    return ok(
        {
            "upcoming_events": [ser(ev) for ev in upcoming_events_rows],
            "all_events": [ser(ev) for ev in all_rows],
            "counts": {"upcoming": upcoming_count, "completed": completed_count},
        },
        **meta,
    )
# ===== CREATE EVENT (POST) with 'upcoming must be future' =====
@api.post("/events")
def api_create_event():
    data = _payload()

    # ---- required: name ----
    name = (get_scalar(request, data, "event_name") or "").strip()
    if not name:
        return err("event_name is required.", 422, "validation_error")

    # ---- required: valid club (non-deleted) ----
    club_id = _coerce_int(
        get_scalar(request, data, "organising_club_id")
        or get_scalar(request, data, "organising_club")
    )
    club = db.session.get(Club, club_id) if club_id else None
    if not club or getattr(club, "is_deleted", False):
        return err("organising_club_id is invalid.", 422, "validation_error")

    # ---- status ----
    status = (get_scalar(request, data, "status") or "upcoming").strip().lower()
    if status not in EVENT_STATUS_VALUES:
        return err("Invalid status.", 422, "validation_error")

    # ---- datetime parsing (accepts split date/time or ISO) ----
    start_at = (
        parse_dt(get_scalar(request, data, "start_date"), get_scalar(request, data, "start_time"))
        or _iso_to_naive(get_scalar(request, data, "start_at"))
    )
    end_at = (
        parse_dt(get_scalar(request, data, "end_date"), get_scalar(request, data, "end_time"))
        or _iso_to_naive(get_scalar(request, data, "end_at"))
    )

    if not start_at:
        return err("Provide start_at (ISO) or start_date + start_time.", 422, "validation_error")
    if end_at and end_at < start_at:
        return err("end_at cannot be before start_at.", 422, "validation_error")

    # ✅ New rule: upcoming must be future
    if status == "upcoming":
        now = datetime.now()  # naive to match parse_dt/_iso_to_naive
        if start_at < now:
            return err(
                f"start_at must be in the future for upcoming events. "
                f"(start_at={start_at.isoformat()}, now={now.isoformat()})",
                422, "validation_error"
            )

    # ---- build row ----
    ev = Event(
        event_name=name,
        organising_club_id=club.club_id,
        event_coordinator=(get_scalar(request, data, "event_coordinator") or "").strip() or None,
        venue=(get_scalar(request, data, "venue") or "").strip() or None,
        start_at=start_at,
        end_at=end_at,
        max_participants=_coerce_int(get_scalar(request, data, "max_participants")),
        status=status,
        description=(get_scalar(request, data, "description") or ""),
    )

    # ---- optional image upload ----
    file = request.files.get("event_image")
    if file and file.filename:
        rel = _save_upload(file, "EVENT_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        ev.event_image = rel

    try:
        db.session.add(ev)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create event")
        return err("Failed to create event.", 500, "db_error")

    return ok({
        "event_id": ev.event_id,
        "event_name": ev.event_name,
        "organising_club_id": ev.organising_club_id,
        "event_coordinator": ev.event_coordinator,
        "venue": ev.venue,
        "start_at": ev.start_at.isoformat() if ev.start_at else None,
        "end_at": ev.end_at.isoformat() if ev.end_at else None,
        "event_image": image_url(ev.event_image) if getattr(ev, "event_image", None) else None,
        "max_participants": ev.max_participants,
        "status": ev.status,
        "description": ev.description or "",
        "created_time": ev.created_time.isoformat() if getattr(ev, "created_time", None) else None,
        "updated_time": ev.updated_time.isoformat() if getattr(ev, "updated_time", None) else None,
    }, 201)

# ===== UPDATE EVENT (PUT) with 'upcoming must be future' =====
@api.put("/events/<int:event_id>")
def api_update_event(event_id):
    ev = db.session.get(Event, event_id)
    if not ev or getattr(ev, "is_deleted", False):
        return err("Event not found or deleted.", 404, "not_found")

    data = _payload()

    # ---- event name (keep existing if not provided) ----
    name = (get_scalar(request, data, "event_name") or "").strip() or ev.event_name

    # ---- club (accept organising_club_id or organising_club) ----
    club_id = (
        _coerce_int(get_scalar(request, data, "organising_club_id"))
        or _coerce_int(get_scalar(request, data, "organising_club"))
        or ev.organising_club_id
    )
    club = db.session.get(Club, club_id) if club_id else None
    if not club or getattr(club, "is_deleted", False):
        return err("Invalid or deleted club.", 422, "validation_error")

    # ---- status ----
    status = (get_scalar(request, data, "status") or ev.status or "upcoming").strip().lower()
    if status not in EVENT_STATUS_VALUES:
        return err("Invalid status.", 422, "validation_error")

    # ---- datetime parsing ----
    new_start_at = (
        parse_dt(get_scalar(request, data, "start_date"), get_scalar(request, data, "start_time"))
        or _iso_to_naive(get_scalar(request, data, "start_at"))
        or ev.start_at
    )

    end_date_in = get_scalar(request, data, "end_date")
    end_time_in = get_scalar(request, data, "end_time")
    end_iso_in  = get_scalar(request, data, "end_at")
    provided_end = (end_date_in is not None) or (end_time_in is not None) or (end_iso_in is not None)

    new_end_at = (
        parse_dt(end_date_in, end_time_in) or _iso_to_naive(end_iso_in)
        if provided_end else ev.end_at
    )

    if new_end_at and new_end_at < new_start_at:
        return err("end_at cannot be before start_at.", 422, "validation_error")

    # ✅ New rule: upcoming must be future
    if status == "upcoming":
        now = datetime.now()
        if new_start_at < now:
            return err(
                f"start_at must be in the future for upcoming events. "
                f"(start_at={new_start_at.isoformat()}, now={now.isoformat()})",
                422, "validation_error"
            )

    # ---- apply fields (keep existing when omitted) ----
    ev.event_name         = name
    ev.organising_club_id = club.club_id
    ev.event_coordinator  = (get_scalar(request, data, "event_coordinator") or "").strip() or ev.event_coordinator
    ev.venue              = (get_scalar(request, data, "venue") or "").strip() or ev.venue
    ev.start_at           = new_start_at
    ev.end_at             = new_end_at

    mp_raw = get_scalar(request, data, "max_participants")
    mp_val = _coerce_int(mp_raw)
    if mp_val is not None:
        ev.max_participants = mp_val

    ev.status = status
    desc_in = get_scalar(request, data, "description")
    if desc_in is not None:
        ev.description = desc_in

    # ---- optional image upload ----
    file = request.files.get("event_image")
    if file and file.filename:
        rel = _save_upload(file, "EVENT_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        ev.event_image = rel

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update event")
        return err("Failed to update event.", 500, "db_error")

    return ok({
        "event_id": ev.event_id,
        "event_name": ev.event_name,
        "organising_club_id": ev.organising_club_id,
        "event_coordinator": ev.event_coordinator,
        "venue": ev.venue,
        "start_at": ev.start_at.isoformat() if ev.start_at else None,
        "end_at": ev.end_at.isoformat() if ev.end_at else None,
        "event_image": image_url(ev.event_image) if getattr(ev, "event_image", None) else None,
        "max_participants": ev.max_participants,
        "status": ev.status,
        "description": ev.description or "",
        "created_time": ev.created_time.isoformat() if getattr(ev, "created_time", None) else None,
        "updated_time": ev.updated_time.isoformat() if getattr(ev, "updated_time", None) else None,
    })


# ===== SOFT DELETE EVENT =====
@api.delete("/events/<int:event_id>")
def api_delete_event(event_id):
    ev = db.session.get(Event, event_id)
    if not ev or getattr(ev, "is_deleted", False):
        return err("Event not found or already deleted.", 404, "not_found")

    ev.is_deleted = True
    ev.deleted_at = func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete event")
        return err("Failed to delete event.", 500, "db_error")

    return ok({
        "id": ev.event_id,
        "message": "Event deleted successfully."
    })



# =====================================================================
# Colleges (GET/POST/PUT/DELETE/RESTORE)
# =====================================================================
@api.get("/colleges")
def api_list_colleges():
    q = _qstr("q")
    status = _qstr("status", "all")
    sort = _qstr("sort", "newest")

    query = College.query.filter(College.is_deleted.is_(False))
    if q:
        query = query.filter(College.college_name.ilike(f"%{q}%"))
    if status in ("active", "inactive"):
        query = query.filter(College.status == status)

    if sort == "name":
        query = query.order_by(College.college_name.asc())
    elif sort == "oldest":
        query = query.order_by(College.created_time.asc(), College.college_id.asc())
    else:
        query = query.order_by(College.created_time.desc(), College.college_id.desc())

    rows, meta = _paginate(query)

    page_ids = [c.college_id for c in rows]
    members_by_college = {}
    if page_ids:
        members_by_college = dict(
            db.session.query(Member.college_id, func.count(Member.member_id))
            .filter(Member.is_deleted.is_(False), (Member.status == "active") | (Member.status.is_(None)), Member.college_id.in_(page_ids))
            .group_by(Member.college_id)
            .all()
        )

    data = [
        {
            "college_id": c.college_id,
            "college_name": c.college_name,
            "members_count": members_by_college.get(c.college_id, 0),
            "clubs_count": 0,
            "email": c.email,
            "location": c.location,
            "status": (c.status or "active").lower(),
            "authority_name": c.authority_name,
            "authority_role": c.authority_role,
            "phone": c.phone,
            "description": c.description,
            "created_time": c.created_time.isoformat() if c.created_time else None,
        }
        for c in rows
    ]

    active_count = db.session.query(func.count(College.college_id)).filter(College.status == "active", College.is_deleted.is_(False)).scalar() or 0
    inactive_count = db.session.query(func.count(College.college_id)).filter(College.status == "inactive", College.is_deleted.is_(False)).scalar() or 0

    return ok({"colleges": data, "counts": {"active": active_count, "inactive": inactive_count}}, **meta)

#POST Colleges
@api.post("/colleges")
def api_create_college():
    data = _payload()

    # ---- required: college name ----
    name = (get_scalar(request, data, "college_name") or "").strip()
    if not name:
        return err("college_name is required.", 422, "validation_error")

    # ---- check duplicates (case-insensitive, non-deleted) ----
    exists = (
        db.session.query(College)
        .filter(College.is_deleted.is_(False), func.lower(College.college_name) == name.lower())
        .first()
    )
    if exists:
        return err("A college with this name already exists.", 409, "conflict")

    # ---- create new college ----
    col = College(
        college_name=name,
        email=(get_scalar(request, data, "email") or "").strip() or None,
        location=(get_scalar(request, data, "location") or "").strip() or None,
        authority_name=(get_scalar(request, data, "authority_name") or "").strip() or None,
        authority_role=clean_role(get_scalar(request, data, "authority_role")),
        phone=clean_phone(get_scalar(request, data, "phone")),
        description=(get_scalar(request, data, "description") or "").strip() or None,
        status=(get_scalar(request, data, "status") or "active").strip().lower(),
    )

    try:
        db.session.add(col)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create college")
        return err("Failed to create college.", 500, "db_error")

    # ---- success: return full created record ----
    return ok({
        "college_id": col.college_id,
        "college_name": col.college_name,
        "email": col.email,
        "location": col.location,
        "authority_name": col.authority_name,
        "authority_role": col.authority_role,
        "phone": col.phone,
        "description": col.description,
        "status": col.status,
        "created_time": col.created_time.isoformat() if getattr(col, "created_time", None) else None,
        "updated_time": col.updated_time.isoformat() if getattr(col, "updated_time", None) else None,
    }, 201)

#Update Colleges
@api.put("/colleges/<int:college_id>")
def api_update_college(college_id: int):
    col = db.session.get(College, college_id)
    if not col or getattr(col, "is_deleted", False):
        return err("College not found or deleted.", 404, "not_found")

    data = _payload()

    # ---- required: name ----
    name = (get_scalar(request, data, "college_name") or "").strip()
    if not name:
        return err("college_name is required.", 422, "validation_error")

    # ---- check duplicate name (case-insensitive, exclude self) ----
    exists = (
        db.session.query(College)
        .filter(
            College.is_deleted.is_(False),
            func.lower(College.college_name) == name.lower(),
            College.college_id != college_id,
        )
        .first()
    )
    if exists:
        return err("Another college with this name already exists.", 409, "conflict")

    # ---- apply updates ----
    col.college_name = name
    col.email = (get_scalar(request, data, "email") or "").strip() or col.email
    col.location = (get_scalar(request, data, "location") or "").strip() or col.location
    col.authority_name = (get_scalar(request, data, "authority_name") or "").strip() or col.authority_name

    role_raw = (get_scalar(request, data, "authority_role") or "").strip() or None
    col.authority_role = clean_role(role_raw) if role_raw is not None else col.authority_role

    phone_raw = (get_scalar(request, data, "phone") or "").strip()
    col.phone = clean_phone(phone_raw) if phone_raw != "" else col.phone

    col.description = (get_scalar(request, data, "description") or "").strip() or col.description

    status = (get_scalar(request, data, "status") or "").strip().lower()
    if status in {"active", "inactive"}:
        col.status = status

    # ---- commit ----
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update college")
        return err("Failed to update college.", 500, "db_error")

    # ---- return full updated data ----
    return ok({
        "college_id": col.college_id,
        "college_name": col.college_name,
        "email": col.email,
        "location": col.location,
        "authority_name": col.authority_name,
        "authority_role": col.authority_role,
        "phone": col.phone,
        "description": col.description,
        "status": col.status,
        "created_time": col.created_time.isoformat() if getattr(col, "created_time", None) else None,
        "updated_time": col.updated_time.isoformat() if getattr(col, "updated_time", None) else None,
    })

#Delete Colleges
@api.delete("/colleges/<int:college_id>")
def api_delete_college(college_id: int):
    college = db.session.get(College, college_id)
    if not college:
        return err("College not found.", 404, "not_found")
    college.is_deleted = True
    college.deleted_at = func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to delete college.", 500, "db_error")
    return ok({"id": college.college_id,
               "message":"College deleted successfully"})


#GET coordinators
# =====================================================================
# Coordinators (GET) — include coordinators even if their club is deleted
# =====================================================================
@api.get("/coordinators")
def api_list_coordinators():
    # filters
    status      = _qstr("status", "all")        # all|active|inactive
    role_type   = _qstr("role_type")
    club_id     = _qint("club_id")
    college_id  = _qint("college_id")
    sort        = _qstr("sort", "newest")       # newest|name
    only_orphan = (request.args.get("only_orphaned", "").strip().lower() in ("1", "true", "yes"))

    # LEFT JOIN club so we can show coordinators even when the club is deleted/missing
    query = (
        db.session.query(Coordinator, Club, College)
        .outerjoin(Club, Coordinator.club_id == Club.club_id)
        .outerjoin(College, Coordinator.college_id == College.college_id)
        .filter(Coordinator.is_deleted.is_(False))
    )

    # apply filters
    if status in ("active", "inactive"):
        query = query.filter(Coordinator.status == status)
    if role_type:
        query = query.filter(Coordinator.role_type == role_type)
    if club_id:
        query = query.filter(Coordinator.club_id == club_id)
    if college_id:
        query = query.filter(Coordinator.college_id == college_id)
    if only_orphan:
        # club missing OR soft-deleted
        query = query.filter((Club.club_id.is_(None)) | (Club.is_deleted.is_(True)))

    # sort
    if sort == "name":
        query = query.order_by(Coordinator.coordinator_name.asc())
    else:
        query = query.order_by(Coordinator.created_time.desc())

    # paginate
    rows, meta = _paginate(query)

    # build payload
    data = []
    for c, club, college in rows:
        # club_deleted = True if club is missing OR present but soft-deleted
        club_deleted = (club is None) or bool(getattr(club, "is_deleted", False))

        data.append({
            "coordinator_id": c.coordinator_id,
            "coordinator_name": c.coordinator_name,
            "club_id": c.club_id,
            "club_name": (club.club_name if club else None),
            "club_deleted": club_deleted,   # <- single flag as requested
            "college_id": c.college_id,
            "college_name": (college.college_name if college and not getattr(college, "is_deleted", False) else None),
            "faculty_dept": c.faculty_dept,
            "role_type": c.role_type,
            "email": c.email,
            "phone": c.phone,
            "description": c.description,
            "status": c.status,
            "image_path": image_url(c.coordinator_image) if c.coordinator_image else None,
            "created_time": c.created_time.isoformat() if getattr(c, "created_time", None) else None,
        })

    # counts (independent of club state)
    student_count = (
        db.session.query(Coordinator)
        .filter(Coordinator.is_deleted.is_(False),
                Coordinator.role_type == "student",
                Coordinator.status == "active")
        .count()
    )
    faculty_like_count = (
        db.session.query(Coordinator)
        .filter(Coordinator.is_deleted.is_(False),
                Coordinator.role_type.in_(["faculty", "lead", "co-lead", "mentor"]),
                Coordinator.status == "active")
        .count()
    )

    # dropdowns: show only non-deleted clubs/colleges
    clubs = Club.query.filter(Club.is_deleted.is_(False)).order_by(Club.club_name.asc()).all()
    colleges = College.query.filter(College.is_deleted.is_(False)).order_by(College.college_name.asc()).all()

    return ok({
        "coordinators": data,
        "counts": {"students": student_count, "faculty_like": faculty_like_count},
        "dropdowns": {
            "clubs": [{"club_id": c.club_id, "club_name": c.club_name} for c in clubs],
            "colleges": [{"college_id": c.college_id, "college_name": c.college_name} for c in colleges],
        },
    }, **meta)

#POST coordinators
@api.post("/coordinators")
def api_create_coordinator():
    data = _payload()

    name = (get_scalar(request, data, "coordinator_name") or "").strip()
    club_id = _coerce_int(get_scalar(request, data, "club_id"))
    if not name:
        return err("coordinator_name is required.", 422, "validation_error")
    if not club_id:
        return err("club_id is required.", 422, "validation_error")

    club = db.session.get(Club, club_id)
    if not club or getattr(club, "is_deleted", False):
        return err("Invalid or deleted club.", 422, "validation_error")

    college_id = _coerce_int(get_scalar(request, data, "college_id"))
    college = None
    if college_id is not None:
        college = db.session.get(College, college_id)
        if not college or getattr(college, "is_deleted", False):
            return err("Invalid or deleted college.", 422, "validation_error")

    co = Coordinator(
        coordinator_name=name,
        club_id=club_id,
        college_id=college_id,
        faculty_dept=(get_scalar(request, data, "faculty_dept") or "").strip() or None,
        role_type=(get_scalar(request, data, "role_type") or "").strip() or None,
        email=(get_scalar(request, data, "email") or "").strip() or None,
        phone=clean_phone(get_scalar(request, data, "phone")),
        description=(get_scalar(request, data, "description") or "").strip() or None,
        status=(get_scalar(request, data, "status") or "active").strip().lower(),
    )

    file = request.files.get("coordinator_image")
    if file and file.filename:
        rel = _save_upload(file, "COORDINATOR_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        co.coordinator_image = rel

    try:
        db.session.add(co)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create coordinator")
        return err("Failed to create coordinator.", 500, "db_error")

    # ✅ return full created record
    return ok({
        "coordinator_id": co.coordinator_id,
        "coordinator_name": co.coordinator_name,
        "club_id": co.club_id,
        "club_name": club.club_name if club else None,
        "college_id": co.college_id,
        "college_name": (college.college_name if college else None),
        "faculty_dept": co.faculty_dept,
        "role_type": co.role_type,
        "email": co.email,
        "phone": co.phone,
        "description": co.description,
        "status": co.status,
        "image": image_url(co.coordinator_image) if getattr(co, "coordinator_image", None) else None,
        "created_time": co.created_time.isoformat() if getattr(co, "created_time", None) else None,
        "updated_time": co.updated_time.isoformat() if getattr(co, "updated_time", None) else None,
    }, 201)

@api.put("/coordinators/<int:coordinator_id>")
def api_update_coordinator(coordinator_id: int):
    co = db.session.get(Coordinator, coordinator_id)
    if not co or getattr(co, "is_deleted", False):
        return err("Coordinator not found or deleted.", 404, "not_found")

    data = _payload()

    # ---- coordinator name ----
    name = (get_scalar(request, data, "coordinator_name") or "").strip()
    if name:
        co.coordinator_name = name

    # ---- club ----
    club_id = _coerce_int(get_scalar(request, data, "club_id"))
    club = None
    if club_id:
        club = db.session.get(Club, club_id)
        if not club or getattr(club, "is_deleted", False):
            return err("Invalid or deleted club.", 422, "validation_error")
        co.club_id = club_id
    else:
        club = db.session.get(Club, co.club_id) if co.club_id else None

    # ---- college ----
    college_id = _coerce_int(get_scalar(request, data, "college_id"))
    college = None
    if college_id is not None:
        college = db.session.get(College, college_id)
        if not college or getattr(college, "is_deleted", False):
            return err("Invalid or deleted college.", 422, "validation_error")
        co.college_id = college_id
    else:
        college = db.session.get(College, co.college_id) if co.college_id else None

    # ---- optional fields ----
    co.faculty_dept = (get_scalar(request, data, "faculty_dept") or "").strip() or co.faculty_dept
    co.role_type = (get_scalar(request, data, "role_type") or "").strip() or co.role_type
    co.email = (get_scalar(request, data, "email") or "").strip() or co.email
    phone = clean_phone(get_scalar(request, data, "phone"))
    if phone:
        co.phone = phone
    co.description = (get_scalar(request, data, "description") or "").strip() or co.description

    # ---- status ----
    status = (get_scalar(request, data, "status") or "").strip().lower()
    if status in {"active", "inactive"}:
        co.status = status

    # ---- image upload ----
    file = request.files.get("coordinator_image")
    if file and file.filename:
        rel = _save_upload(file, "COORDINATOR_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        co.coordinator_image = rel

    # ---- commit ----
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update coordinator")
        return err("Failed to update coordinator.", 500, "db_error")

    # ---- full success response ----
    return ok({
        "coordinator_id": co.coordinator_id,
        "coordinator_name": co.coordinator_name,
        "club_id": co.club_id,
        "club_name": club.club_name if club else None,
        "college_id": co.college_id,
        "college_name": college.college_name if college else None,
        "faculty_dept": co.faculty_dept,
        "role_type": co.role_type,
        "email": co.email,
        "phone": co.phone,
        "description": co.description,
        "status": co.status,
        "image": image_url(co.coordinator_image) if getattr(co, "coordinator_image", None) else None,
        "created_time": co.created_time.isoformat() if getattr(co, "created_time", None) else None,
        "updated_time": co.updated_time.isoformat() if getattr(co, "updated_time", None) else None,
    })
#Delete coordinators
@api.delete("/coordinators/<int:coordinator_id>")
def api_delete_coordinator(coordinator_id: int):
    co = db.session.get(Coordinator, coordinator_id)
    if not co or getattr(co, "is_deleted", False):
        return err("Coordinator not found or already deleted.", 404, "not_found")

    co.is_deleted = True
    co.deleted_at = func.now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete coordinator")
        return err("Failed to delete coordinator.", 500, "db_error")

    return ok({
        "id": co.coordinator_id,
        "message": f"Coordinator '{co.coordinator_name}' deleted successfully."
    }, 200)

# =====================================================================
# Members (GET/POST/PUT/DELETE/RESTORE) — distinct pagination fix
# =====================================================================
@api.get("/members")
def api_list_members():
    q = _qstr("q")
    status_filter = _qstr("status", "all")
    sort_by = _qstr("sort", "newest")
    include_set = {s.strip().lower() for s in (_qstr("include") or "").split(",") if s}

    raw_club_ids = request.args.getlist("club_ids")
    club_ids = [int(cid) for cid in raw_club_ids if str(cid).isdigit()]

    base = db.session.query(Member).filter(Member.is_deleted.is_(False))

    if q:
        base = base.filter(Member.member_name.ilike(f"%{q}%"))

    if club_ids:
        base = (
            base.join(member_clubs, Member.member_id == member_clubs.c.member_id)
            .join(Club, member_clubs.c.club_id == Club.club_id)
            .filter(Club.is_deleted.is_(False), member_clubs.c.club_id.in_(club_ids))
        )

    if status_filter == "active":
        base = base.filter((func.lower(Member.status) == "active") | (Member.status.is_(None)))
    elif status_filter == "inactive":
        base = base.filter(func.lower(Member.status) == "inactive")

    # sorting on base
    if sort_by == "name":
        base = base.order_by(Member.member_name.asc())
    elif sort_by == "oldest":
        base = base.order_by(Member.created_time.asc())
    else:
        base = base.order_by(Member.created_time.desc())

    # distinct members to avoid duplicates due to M2M
    base = base.distinct(Member.member_id)

    page_rows, meta = _paginate(base)
    member_ids = [m.member_id for m in page_rows]

    members = (
        db.session.query(Member)
        .options(selectinload(Member.college), selectinload(Member.clubs))
        .filter(Member.member_id.in_(member_ids))
        .all()
    )
    by_id = {m.member_id: m for m in members}
    ordered = [by_id[i] for i in member_ids if i in by_id]

    data = []
    for m in ordered:
        visible_clubs = [c for c in m.clubs if not getattr(c, "is_deleted", False)]
        data.append(
            {
                "id": m.member_id,
                "name": m.member_name,
                "club": ", ".join([c.club_name for c in visible_clubs]) if visible_clubs else "-",
                "college": m.college.college_name if m.college and not m.college.is_deleted else "-",
                "college_id": m.college_id,
                "faculty_dept": m.faculty_dept,
                "email": m.email,
                "phone": m.phone,
                "image_path": image_url(m.member_image) if m.member_image else None,
                "description": m.description,
                "status": m.status,
                "club_ids": [c.club_id for c in visible_clubs],
                "created_time": m.created_time.isoformat() if m.created_time else None,
            }
        )

    total_members = db.session.query(func.count(Member.member_id)).filter(Member.is_deleted.is_(False)).scalar() or 0
    active_members = (
        db.session.query(func.count(Member.member_id))
        .filter(Member.is_deleted.is_(False), (Member.status == "active") | (Member.status.is_(None)))
        .scalar()
        or 0
    )
    inactive_members = total_members - active_members

    payload = {
        "members": data,
        "counts": {"total": total_members, "active": active_members, "inactive": inactive_members},
    }

    if "dropdowns" in include_set:
        clubs = Club.query.filter(Club.is_deleted.is_(False)).order_by(Club.club_name.asc()).all()
        colleges = College.query.filter(College.is_deleted.is_(False)).order_by(College.college_name.asc()).all()
        payload["dropdowns"] = {
            "clubs": [{"club_id": c.club_id, "club_name": c.club_name} for c in clubs],
            "colleges": [{"college_id": c.college_id, "college_name": c.college_name} for c in colleges],
        }

    return ok(payload, **meta)

#POST members
@api.post("/members")
def api_create_member():
    data = _payload()

    # ---- required: name ----
    name = (get_scalar(request, data, "member_name") or "").strip()
    if not name:
        return err("member_name is required.", 422, "validation_error")

    # ---- required: at least one valid (non-deleted) club ----
    raw_ids = get_list(request, data, "club_ids")
    club_ids = sorted({int(x) for x in raw_ids if str(x).isdigit()})
    if not club_ids:
        return err("At least one club_id is required.", 422, "validation_error")

    clubs = Club.query.filter(
        Club.club_id.in_(club_ids),
        Club.is_deleted.is_(False)
    ).all()
    if len(clubs) != len(club_ids):
        return err("One or more clubs are invalid/deleted.", 422, "validation_error")

    # ---- optional college (must be non-deleted if provided) ----
    college_id = _coerce_int(get_scalar(request, data, "college_id"))
    college = None
    if college_id is not None:
        college = College.query.filter(
            College.college_id == college_id,
            College.is_deleted.is_(False)
        ).first()
        if not college:
            return err("Invalid/deleted college.", 422, "validation_error")

    # ---- optional fields ----
    faculty_dept = (get_scalar(request, data, "faculty_dept") or "").strip() or None
    email        = (get_scalar(request, data, "email") or "").strip() or None
    phone        = clean_phone(get_scalar(request, data, "phone"))
    description  = (get_scalar(request, data, "description") or "").strip() or None
    status       = (get_scalar(request, data, "status") or "active").strip().lower()

    # ---- optional image (multipart only) ----
    image_rel_path = None
    file = request.files.get("member_image")
    if file and file.filename:
        rel = _save_upload(file, "MEMBER_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        image_rel_path = rel

    # ---- insert member + associations ----
    try:
        mem = Member(
            member_name=name,
            college_id=college_id,
            faculty_dept=faculty_dept,
            email=email,
            phone=phone,
            member_image=image_rel_path,
            description=description,
            status=status,
        )
        db.session.add(mem)
        db.session.flush()  # get mem.member_id for association rows

        # add club associations (keep using the already-validated 'clubs' list)
        for c in clubs:
            db.session.execute(
                member_clubs.insert().values(
                    member_id=mem.member_id,
                    club_id=c.club_id,
                    joined_date=func.now()
                )
            )

        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create member")
        return err("Failed to create member.", 500, "db_error")

    # ---- build full response (use local 'clubs' & 'college' to avoid reloading) ----
    return ok({
        "member_id": mem.member_id,
        "member_name": mem.member_name,
        "college_id": mem.college_id,
        "college_name": (college.college_name if college else None),
        "faculty_dept": mem.faculty_dept,
        "email": mem.email,
        "phone": mem.phone,
        "image_path": image_url(mem.member_image) if getattr(mem, "member_image", None) else None,
        "description": mem.description or "",
        "status": mem.status,
        "clubs": [{"club_id": c.club_id, "club_name": c.club_name} for c in clubs],
        "created_time": mem.created_time.isoformat() if getattr(mem, "created_time", None) else None,
        "updated_time": mem.updated_time.isoformat() if getattr(mem, "updated_time", None) else None,
    }, 201)

# Update Members
@api.put("/members/<int:member_id>")
def api_update_member(member_id: int):
    m = db.session.get(Member, member_id)
    if not m or getattr(m, "is_deleted", False):
        return err("Member not found or deleted.", 404, "not_found")

    data = _payload()

    # --- name ---
    name = (get_scalar(request, data, "member_name") or "").strip()
    if name:
        m.member_name = name

    # --- college (0 means unset/None) ---
    college_id = _coerce_int(get_scalar(request, data, "college_id"))
    if college_id is not None:
        if college_id == 0:
            m.college_id = None
        else:
            college = College.query.filter(
                College.college_id == college_id,
                College.is_deleted.is_(False)
            ).first()
            if not college:
                return err("Invalid/deleted college.", 422, "validation_error")
            m.college_id = college_id

    # --- simple fields ---
    fac = (get_scalar(request, data, "faculty_dept") or "").strip()
    if fac:
        m.faculty_dept = fac

    email_in = (get_scalar(request, data, "email") or "").strip()
    if email_in:
        m.email = email_in

    phone = clean_phone(get_scalar(request, data, "phone"))
    if phone is not None:
        m.phone = phone

    # ✅ description: update if key is present (allows clearing to "")
    if "description" in (data or {}):
        desc_in = get_scalar(request, data, "description")
        m.description = (desc_in or "").strip()

    status = (get_scalar(request, data, "status") or "").strip().lower()
    if status in {"active", "inactive"}:
        m.status = status

    # --- clubs replace (if provided) ---
    raw_ids = get_list(request, data, "club_ids")
    if raw_ids:
        club_ids = sorted({int(x) for x in raw_ids if str(x).isdigit()})
        clubs = Club.query.filter(
            Club.club_id.in_(club_ids),
            Club.is_deleted.is_(False)
        ).all()
        if len(clubs) != len(club_ids):
            return err("One or more clubs are invalid/deleted.", 422, "validation_error")

        db.session.execute(
            member_clubs.delete().where(member_clubs.c.member_id == m.member_id)
        )
        for c in clubs:
            db.session.execute(
                member_clubs.insert().values(
                    member_id=m.member_id,
                    club_id=c.club_id,
                    joined_date=func.now()
                )
            )

    # --- optional image upload ---
    file = request.files.get("member_image")
    if file and file.filename:
        rel = _save_upload(file, "MEMBER_UPLOAD_FOLDER")
        if not rel:
            return err("Invalid image format.", 415, "unsupported_media")
        m.member_image = rel

    try:
        db.session.commit()
        # ensure relationships/timestamps are fresh for response
        db.session.refresh(m)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update member")
        return err("Failed to update member.", 500, "db_error")

    college = College.query.get(m.college_id) if m.college_id else None

    # If you want guaranteed fresh clubs after raw inserts:
    clubs_q = (
        db.session.query(Club)
        .join(member_clubs, member_clubs.c.club_id == Club.club_id)
        .filter(member_clubs.c.member_id == m.member_id, Club.is_deleted.is_(False))
        .order_by(Club.club_name.asc())
        .all()
    )

    return ok({
        "member_id": m.member_id,
        "member_name": m.member_name,
        "college_id": m.college_id,
        "college_name": (college.college_name if college and not getattr(college, "is_deleted", False) else None),
        "faculty_dept": m.faculty_dept,
        "email": m.email,
        "phone": m.phone,
        "image_path": image_url(m.member_image) if getattr(m, "member_image", None) else None,
        "description": m.description or "",
        "status": m.status,
        "clubs": [{"club_id": c.club_id, "club_name": c.club_name} for c in clubs_q],
        "created_time": m.created_time.isoformat() if getattr(m, "created_time", None) else None,
        "updated_time": m.updated_time.isoformat() if getattr(m, "updated_time", None) else None,
        "message": "Member updated successfully."
    })

#Delete Members
@api.delete("/members/<int:member_id>")
def api_delete_member(member_id: int):
    m = db.session.get(Member, member_id)
    if not m or getattr(m, "is_deleted", False):
        return err("Member not found or already deleted.", 404, "not_found")

    m.is_deleted = True
    m.deleted_at = func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete member")
        return err("Failed to delete member.", 500, "db_error")

    return ok({
        "id": m.member_id,
        "message": f"Member '{m.member_name}' deleted successfully."
    })

# =====================================================================
# Announcements (GET/POST/PUT/DELETE/RESTORE) — boolean parsing fixed
# =====================================================================
@api.get("/announcements")
def api_list_announcements():
    q = _qstr("q")
    club_id = _qint("club_id")
    status = _qstr("status")
    sort = _qstr("sort", "pinned")
    include = {s.strip().lower() for s in (_qstr("include") or "").split(",") if s}
    pinned_s = _qstr("pinned")
    pinned = None
    if pinned_s:
        pb = _parse_bool(pinned_s)
        if pb is not None:
            pinned = pb

    query = Announcement.query.filter(Announcement.is_deleted.is_(False))
    if q:
        query = query.filter(or_(Announcement.title.ilike(f"%{q}%"), Announcement.content.ilike(f"%{q}%")))
    if club_id:
        query = query.filter(Announcement.club_id == club_id)
    if status:
        query = query.filter(Announcement.status == status)
    if pinned is not None:
        query = query.filter(Announcement.pinned == pinned)

    created_col = getattr(Announcement, "created_time", None)
    updated_col = getattr(Announcement, "updated_at", None)

    if sort == "updated" and updated_col is not None:
        query = query.order_by(Announcement.pinned.desc(), updated_col.desc())
    elif sort == "newest" and created_col is not None:
        query = query.order_by(Announcement.pinned.desc(), created_col.desc())
    elif sort == "oldest" and created_col is not None:
        query = query.order_by(Announcement.pinned.desc(), created_col.asc())
    else:
        if updated_col is not None:
            query = query.order_by(Announcement.pinned.desc(), updated_col.desc())
        else:
            query = query.order_by(Announcement.pinned.desc())

    rows, meta = _paginate(query)

    def ser(a: Announcement):
        return {
            "id": a.id,
            "club_id": a.club_id,
            "title": a.title,
            "content": a.content,
            "publish_at": a.publish_at.isoformat() if a.publish_at else None,
            "expire_at": a.expire_at.isoformat() if a.expire_at else None,
            "priority": a.priority,
            "audience": a.audience,
            "status": a.status,
            "send_email": bool(a.send_email),
            "pinned": bool(a.pinned),
            "updated_at": a.updated_at.isoformat() if getattr(a, "updated_at", None) else None,
            "created_time": a.created_time.isoformat() if getattr(a, "created_time", None) else None,
        }

    payload = {"announcements": [ser(a) for a in rows]}

    if "dropdowns" in include:
        clubs = Club.query.filter(Club.is_deleted.is_(False)).order_by(Club.club_name.asc()).all()
        payload["dropdowns"] = {"clubs": [{"club_id": c.club_id, "club_name": c.club_name} for c in clubs]}

    return ok(payload, **meta)

#Create Announcements
@api.post("/announcements")
def api_create_announcement():
    data = _payload()

    # ---- Required fields ----
    title = (get_scalar(request, data, "title") or "").strip()
    content = (get_scalar(request, data, "content") or "").strip()
    if not title:
        return err("title is required.", 422, "validation_error")
    if not content:
        return err("content is required.", 422, "validation_error")

    # ---- Club validation (optional) ----
    club_id = _coerce_int(get_scalar(request, data, "club_id"))
    club = None
    if club_id is not None:
        club = db.session.get(Club, club_id)
        if not club or getattr(club, "is_deleted", False):
            return err("Invalid or deleted club.", 422, "validation_error")

    # ---- Date/time validation ----
    publish_at = (
        parse_dt(get_scalar(request, data, "publish_date"), get_scalar(request, data, "publish_time"))
        or _iso_to_naive(get_scalar(request, data, "publish_at"))
    )
    expire_at = (
        parse_dt(get_scalar(request, data, "expire_date"), get_scalar(request, data, "expire_time"))
        or _iso_to_naive(get_scalar(request, data, "expire_at"))
    )

    status = (get_scalar(request, data, "status") or "draft").strip().lower()
    if status not in {"draft", "published"}:
        return err("Invalid status.", 422, "validation_error")
    if status == "published" and not publish_at:
        return err("publish_at is required to publish.", 422, "validation_error")
    if publish_at and expire_at and expire_at <= publish_at:
        return err("expire_at must be after publish_at.", 422, "validation_error")

    # ---- Boolean conversions ----
    se = _parse_bool(get_scalar(request, data, "send_email"))
    pn = _parse_bool(get_scalar(request, data, "pinned"))

    # ---- Create announcement ----
    ann = Announcement(
        club_id=club.club_id if club else None,
        title=title,
        content=content,
        publish_at=publish_at,
        expire_at=expire_at,
        priority=(get_scalar(request, data, "priority") or "normal").strip().lower(),
        audience=(get_scalar(request, data, "audience") or "all_members").strip().lower(),
        status=status,
        send_email=bool(se) if se is not None else False,
        pinned=bool(pn) if pn is not None else False,
    )

    try:
        db.session.add(ann)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create announcement")
        return err("Failed to create announcement.", 500, "db_error")

    # ---- Response with full data ----
    return ok({
        "id": ann.id,
        "title": ann.title,
        "content": ann.content,
        "club_id": ann.club_id,
        "club_name": club.club_name if club else None,
        "publish_at": ann.publish_at.isoformat() if ann.publish_at else None,
        "expire_at": ann.expire_at.isoformat() if ann.expire_at else None,
        "priority": ann.priority,
        "audience": ann.audience,
        "status": ann.status,
        "send_email": ann.send_email,
        "pinned": ann.pinned,
        "created_at": ann.created_at.isoformat() if getattr(ann, "created_at", None) else None,
        "updated_at": ann.updated_at.isoformat() if getattr(ann, "updated_at", None) else None,
        "message": "Announcement created successfully."
    }, 201)
#Update Announcements
# ===== UPDATE ANNOUNCEMENT (full response) =====
@api.put("/announcements/<int:ann_id>")
def api_update_announcement(ann_id: int):
    ann = db.session.get(Announcement, ann_id)
    if not ann or getattr(ann, "is_deleted", False):
        return err("Announcement not found or deleted.", 404, "not_found")

    data = _payload()

    # ---- core fields (keep existing when omitted/blank) ----
    title   = (get_scalar(request, data, "title") or "").strip() or ann.title
    content = (get_scalar(request, data, "content") or "").strip() or ann.content

    # ---- club (optional) ----
    club_id = _coerce_int(get_scalar(request, data, "club_id"))
    club = None
    if club_id is not None:
        club = db.session.get(Club, club_id)
        if not club or getattr(club, "is_deleted", False):
            return err("Invalid or deleted club.", 422, "validation_error")

    # ---- datetimes (accept ISO or date+time pairs) ----
    publish_at = (
        _iso_to_naive(get_scalar(request, data, "publish_at"))
        or parse_dt(get_scalar(request, data, "publish_date"), get_scalar(request, data, "publish_time"))
        or ann.publish_at
    )
    expire_at = (
        _iso_to_naive(get_scalar(request, data, "expire_at"))
        or parse_dt(get_scalar(request, data, "expire_date"), get_scalar(request, data, "expire_time"))
        or ann.expire_at
    )

    # ---- status / priority / audience ----
    status = (get_scalar(request, data, "status") or ann.status or "draft").strip().lower()
    if status not in {"draft", "published"}:
        return err("Invalid status.", 422, "validation_error")
    if status == "published" and not publish_at:
        return err("publish_at is required to publish.", 422, "validation_error")
    if publish_at and expire_at and expire_at <= publish_at:
        return err("expire_at must be after publish_at.", 422, "validation_error")

    priority = (get_scalar(request, data, "priority") or ann.priority or "normal").strip().lower()
    if priority not in {"normal", "high", "urgent"}:
        priority = "normal"
    audience = (get_scalar(request, data, "audience") or ann.audience or "all_members").strip().lower()

    # ---- booleans (only update if provided) ----
    se = _parse_bool(get_scalar(request, data, "send_email"))
    pn = _parse_bool(get_scalar(request, data, "pinned"))

    # ---- apply ----
    ann.title      = title
    ann.content    = content
    if club_id is not None:
        ann.club_id = club_id
    ann.publish_at = publish_at
    ann.expire_at  = expire_at
    ann.priority   = priority
    ann.audience   = audience
    ann.status     = status
    if se is not None:
        ann.send_email = se
    if pn is not None:
        ann.pinned = pn

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to update announcement")
        return err("Failed to update announcement.", 500, "db_error")

    # fetch club name safely for response
    club_for_resp = db.session.get(Club, ann.club_id) if ann.club_id else None

    return ok({
        "id": ann.id,
        "title": ann.title,
        "content": ann.content,
        "club_id": ann.club_id,
        "club_name": (club_for_resp.club_name if club_for_resp and not getattr(club_for_resp, "is_deleted", False) else None),
        "publish_at": ann.publish_at.isoformat() if ann.publish_at else None,
        "expire_at": ann.expire_at.isoformat() if ann.expire_at else None,
        "priority": ann.priority,
        "audience": ann.audience,
        "status": ann.status,
        "send_email": bool(ann.send_email),
        "pinned": bool(ann.pinned),
        "created_at": ann.created_time.isoformat() if getattr(ann, "created_time", None) else None,
        "updated_at": ann.updated_time.isoformat() if getattr(ann, "updated_time", None) else None,
        "message": "Announcement updated successfully."
    })

#Delete Announcements
@api.delete("/announcements/<int:ann_id>")
def api_delete_announcement(ann_id: int):
    ann = db.session.get(Announcement, ann_id)
    if not ann or getattr(ann, "is_deleted", False):
        return err("Announcement not found or already deleted.", 404, "not_found")

    ann.is_deleted = True
    ann.deleted_at = func.now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete announcement")
        return err("Failed to delete announcement.", 500, "db_error")

    return ok({
        "id": ann.id,
        "message": f"Announcement '{ann.title}' deleted successfully."
    }, 200)

