# app/api.py — API twin of routes.py
from __future__ import annotations
import os
from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import func, desc
from models import db, Club, Event, Coordinator, College, Announcement  # absolute imports!

api = Blueprint("api", __name__, url_prefix="/api")

# -------- helpers --------
def ok(data: Any = None, status: int = 200, **meta):
    payload = {"ok": True, "data": data}
    if meta:
        payload["meta"] = meta
    return jsonify(payload), status

def err(message: str, status: int = 400, code: str = "bad_request"):
    return jsonify({"ok": False, "error": {"code": code, "message": message}}), status

def image_url(relpath: str | None):
    if not relpath:
        return None
    return url_for("static", filename=relpath, _external=True)

def _parse_dt(date_str: str | None, time_str: str | None):
    # Mirrors utils.parse_dt behavior (YYYY-MM-DD + HH:MM)
    if not date_str or not time_str:
        return None
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except Exception:
        return None

# -------- health --------
@api.get("/health")
def health():
    return ok({"service": "ai-nexus", "status": "up", "time": datetime.now().isoformat(timespec="seconds")})

# =========================
# Dashboard (mirror of index)
# =========================
@api.get("/dashboard")
def dashboard():
    # Card counts (same logic you use in index())
    active_clubs = db.session.query(func.count(Club.club_id)).filter(Club.status == "active").scalar() or 0
    active_colleges = db.session.query(func.count(College.college_id)).filter(College.status == "active").scalar() or 0
    active_coordinators = db.session.query(func.count(Coordinator.coordinator_id)).filter(Coordinator.status == "active").scalar() or 0

    # You count "upcoming" by status == upcoming on the homepage
    upcoming_events_count = db.session.query(func.count(Event.event_id)).filter(Event.status == "upcoming").scalar() or 0

    # Recent clubs (latest 2)
    clubs = Club.query.order_by(Club.club_id.desc()).limit(2).all()
    recent_clubs = [{"name": c.club_name, "created_time": getattr(c, "created_time", None)} for c in clubs]

    # Nearest upcoming 2 (status upcoming + start >= now), soonest first
    now_local = datetime.now()
    upcoming_rows = (
        Event.query.filter(Event.status == "upcoming", Event.start_at >= now_local)
        .order_by(Event.start_at.asc()).limit(2).all()
    )
    upcoming_events = [
        {
            "name": ev.event_name,
            "description": ev.description or "",
            "start_at": ev.start_at.isoformat() if getattr(ev, "start_at", None) else None,
        }
        for ev in upcoming_rows
    ]

    # Recent activities (latest 2 by created_time)
    recent_events_rows = Event.query.order_by(Event.created_time.desc()).limit(2).all()
    recent_events = [
        {
            "name": ev.event_name,
            "created_time": ev.created_time.isoformat() if getattr(ev, "created_time", None) else None,
        }
        for ev in recent_events_rows
    ]

    return ok({
        "cards": {
            "active_clubs": active_clubs,
            "active_colleges": active_colleges,
            "active_coordinators": active_coordinators,
            "upcoming_events": upcoming_events_count,
        },
        "recent_clubs": recent_clubs,
        "upcoming_events": upcoming_events,
        "recent_events": recent_events,
    })

# =========================
# Clubs
# =========================
@api.get("/clubs")
def api_list_clubs():
    rows = Club.query.order_by(Club.club_name.asc()).all()
    data = [{
        "club_id": c.club_id,
        "club_name": c.club_name,
        "club_category": c.club_category,
        "coordinator": c.coordinator,
        "coordinator_type": c.coordinator_type,
        "status": c.status,
        "description": c.description or "",
        "club_logo": image_url(c.club_logo),
        "created_time": c.created_time.isoformat() if getattr(c, "created_time", None) else None,
        "updated_time": c.updated_time.isoformat() if getattr(c, "updated_time", None) else None,
    } for c in rows]
    return ok(data)

@api.post("/clubs")
def api_create_club():
    p = request.get_json(silent=True) or {}
    club_name = (p.get("club_name") or "").strip()
    if not club_name:
        return err("club_name is required.", 422, "validation_error")

    club = Club(
        club_name=club_name,
        club_category=(p.get("club_category") or "").strip() or None,
        coordinator=(p.get("coordinator") or "").strip() or None,
        coordinator_type=(p.get("coordinator_type") or "").strip() or None,
        description=p.get("description") or "",
        status=(p.get("status") or "active").strip().lower()
    )
    try:
        db.session.add(club)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to create club.", 500, "db_error")
    return ok({"club_id": club.club_id}, 201)

@api.patch("/clubs/<int:club_id>")
def api_update_club(club_id: int):
    c = db.session.get(Club, club_id)
    if not c:
        return err("Club not found.", 404, "not_found")
    p = request.get_json(silent=True) or {}
    for key in ("club_name", "club_category", "coordinator", "coordinator_type", "description", "status"):
        if key in p:
            setattr(c, key, (p.get(key) or None))
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to update club.", 500, "db_error")
    return ok({"club_id": c.club_id})

# =========================
# Events
# =========================
@api.get("/events")
def api_list_events():
    now_local = datetime.now()
    # To mirror /events page: show all, ordered by start_at desc
    all_events = Event.query.order_by(Event.start_at.desc()).all()

    # Also include the page widgets’ counts & upcoming 3 (same logic)
    upcoming_events = (
        Event.query
        .filter(Event.status != "cancelled", Event.start_at >= now_local)
        .order_by(Event.start_at.asc())
        .limit(3).all()
    )
    upcoming_count = (
        db.session.query(Event)
        .filter(Event.status != "cancelled", Event.start_at >= now_local)
        .count()
    )
    completed_count = db.session.query(Event).filter(Event.status == "completed").count()

    def serialize(ev: Event):
        return {
            "event_id": ev.event_id,
            "event_name": ev.event_name,
            "organising_club_id": ev.organising_club_id,
            "event_coordinator": ev.event_coordinator,
            "venue": ev.venue,
            "start_at": ev.start_at.isoformat() if getattr(ev, "start_at", None) else None,
            "end_at": ev.end_at.isoformat() if getattr(ev, "end_at", None) else None,
            "event_image": image_url(ev.event_image),
            "max_participants": ev.max_participants,
            "status": ev.status,
            "description": ev.description or "",
            "created_time": ev.created_time.isoformat() if getattr(ev, "created_time", None) else None,
        }

    return ok({
        "upcoming_events": [serialize(ev) for ev in upcoming_events],
        "all_events": [serialize(ev) for ev in all_events],
        "counts": {"upcoming": upcoming_count, "completed": completed_count}
    })

@api.post("/events")
def api_create_event():
    p = request.get_json(silent=True) or {}
    EVENT_STATUS_VALUES = {"upcoming", "completed", "cancelled"}

    name = (p.get("event_name") or "").strip()
    if not name:
        return err("event_name is required.", 422, "validation_error")

    club_id = p.get("organising_club_id")
    if not club_id or not db.session.get(Club, club_id):
        return err("organising_club_id is invalid.", 422, "validation_error")

    status = (p.get("status") or "upcoming").strip().lower()
    if status not in EVENT_STATUS_VALUES:
        return err("Invalid status.", 422, "validation_error")

    # mirror parse_dt style: accept "YYYY-MM-DD" + "HH:MM" OR ISO strings
    def _parse_any(val_date, val_time):
        if val_date and val_time:
            return _parse_dt(val_date, val_time)
        s = (val_date or val_time or "").strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    start_at = _parse_any(p.get("start_date"), p.get("start_time")) or _parse_any(p.get("start_at"), None)
    end_at   = _parse_any(p.get("end_date"),   p.get("end_time"))   or _parse_any(p.get("end_at"),   None)

    if not start_at or not end_at:
        return err("start_at and end_at are required.", 422, "validation_error")
    if end_at <= start_at:
        return err("end_at must be after start_at.", 422, "validation_error")

    ev = Event(
        event_name=name,
        organising_club_id=club_id,
        event_coordinator=(p.get("event_coordinator") or "").strip() or None,
        venue=(p.get("venue") or "").strip() or None,
        start_at=start_at,
        end_at=end_at,
        event_image=(p.get("event_image") or "").strip() or None,
        max_participants=p.get("max_participants"),
        status=status,
        description=p.get("description") or "",
    )
    try:
        db.session.add(ev)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to create event.", 500, "db_error")
    return ok({"event_id": ev.event_id}, 201)

# =========================
# Colleges
# =========================
@api.get("/colleges")
def api_list_colleges():
    rows = College.query.order_by(College.college_name.asc()).all()
    data = [{
        "college_id": c.college_id,
        "college_name": c.college_name,
        "members_count": 0,
        "clubs_count": 0,
        "email": c.email,
        "location": c.location,
        "status": (c.status or "active").lower(),
        "authority_name": c.authority_name,
        "authority_role": c.authority_role,
        "phone": c.phone,
        "description": c.description,
        "created_time": c.created_time.isoformat() if getattr(c, "created_time", None) else None,
    } for c in rows]
    active_count = sum(1 for r in rows if (r.status or "active").lower() == "active")
    inactive_count = len(rows) - active_count
    return ok({"colleges": data, "counts": {"active": active_count, "inactive": inactive_count}})

@api.post("/colleges")
def api_create_college():
    p = request.get_json(silent=True) or {}
    name = (p.get("college_name") or "").strip()
    if not name:
        return err("college_name is required.", 422, "validation_error")

    exists = College.query.filter(func.lower(College.college_name) == name.lower()).first()
    if exists:
        return err("A college with this name already exists.", 409, "conflict")

    col = College(
        college_name=name,
        authority_name=(p.get("authority_name") or "").strip() or None,
        authority_role=(p.get("authority_role") or "").strip() or None,
        phone=(p.get("phone") or "").strip() or None,
        description=p.get("description") or None,
        email=(p.get("email") or "").strip() or None,
        location=(p.get("location") or "").strip() or None,
        status="active",
    )
    try:
        db.session.add(col)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to create college.", 500, "db_error")
    return ok({"college_id": col.college_id}, 201)

# =========================
# Coordinators
# =========================
@api.get("/coordinators")
def api_list_coordinators():
    rows = (
        db.session.query(Coordinator, Club, College)
        .join(Club, Coordinator.club_id == Club.club_id)
        .outerjoin(College, Coordinator.college_id == College.college_id)
        .filter(Coordinator.status == "active")
        .order_by(Coordinator.created_time.desc())
        .all()
    )
    data = []
    for coord, club, college in rows:
        data.append({
            "coordinator_id": coord.coordinator_id,
            "coordinator_name": coord.coordinator_name,
            "club": club.club_name if club else None,
            "role_type": coord.role_type or None,
            "college_or_dept": coord.faculty_dept,  # mirrors your template choice
            "email": coord.email,
            "phone": coord.phone,
            "image": image_url(coord.coordinator_image),
            "status": coord.status,
            "created_time": coord.created_time.isoformat() if getattr(coord, "created_time", None) else None,
        })
    stats = {
        "students": db.session.query(Coordinator)
            .filter(Coordinator.role_type == "student", Coordinator.status == "active").count(),
        "faculty_like": db.session.query(Coordinator)
            .filter(Coordinator.role_type.in_(["faculty", "lead", "co-lead", "mentor"]),
                    Coordinator.status == "active").count(),
    }
    return ok({"coordinators": data, "counts": stats})

@api.post("/coordinators")
def api_create_coordinator():
    p = request.get_json(silent=True) or {}
    name = (p.get("coordinator_name") or "").strip()
    club_id = p.get("club_id")
    if not name:
        return err("coordinator_name is required.", 422, "validation_error")
    if not club_id or not db.session.get(Club, club_id):
        return err("club_id is invalid.", 422, "validation_error")

    college_id = p.get("college_id")
    if college_id and not db.session.get(College, college_id):
        college_id = None

    co = Coordinator(
        coordinator_name=name,
        club_id=club_id,
        college_id=college_id,
        faculty_dept=(p.get("faculty_dept") or "").strip() or None,
        role_type=(p.get("role_type") or "").strip() or None,
        email=(p.get("email") or "").strip() or None,
        phone=(p.get("phone") or "").strip() or None,
        coordinator_image=(p.get("coordinator_image") or "").strip() or None,
        description=p.get("description") or None,
        status="active",
    )
    try:
        db.session.add(co)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to create coordinator.", 500, "db_error")
    return ok({"coordinator_id": co.coordinator_id}, 201)

# =========================
# Announcements
# =========================
@api.get("/announcements")
def api_list_announcements():
    # Pinned first, then non-NULL publish_at (newest), NULLs last — same as routes.py
    rows = (
        Announcement.query
        .order_by(
            Announcement.pinned.desc(),
            Announcement.publish_at.is_(None),
            Announcement.publish_at.desc()
        ).all()
    )
    data = [{
        "id": a.id,
        "club_id": a.club_id,
        "title": a.title,
        "content": a.content,
        "publish_at": a.publish_at.isoformat() if getattr(a, "publish_at", None) else None,
        "expire_at": a.expire_at.isoformat() if getattr(a, "expire_at", None) else None,
        "priority": a.priority,
        "audience": a.audience,
        "status": a.status,
        "send_email": a.send_email,
        "pinned": a.pinned,
    } for a in rows]
    return ok(data)

@api.post("/announcements")
def api_create_announcement():
    p = request.get_json(silent=True) or {}
    title = (p.get("title") or "").strip()
    content = (p.get("content") or "").strip()
    status = (p.get("status") or "draft").strip()
    if not title:
        return err("title is required.", 422, "validation_error")
    if not content:
        return err("content is required.", 422, "validation_error")
    if status == "published" and not (p.get("publish_date") and p.get("publish_time")) and not p.get("publish_at"):
        return err("publish_at (or publish_date+publish_time) required to publish.", 422, "validation_error")

    publish_at = _parse_dt(p.get("publish_date"), p.get("publish_time")) if p.get("publish_date") else None
    if not publish_at and p.get("publish_at"):
        try:
            publish_at = datetime.fromisoformat(str(p["publish_at"]).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            publish_at = None
    expire_at = _parse_dt(p.get("expire_date"), p.get("expire_time")) if p.get("expire_date") else None
    if not expire_at and p.get("expire_at"):
        try:
            expire_at = datetime.fromisoformat(str(p["expire_at"]).replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            expire_at = None

    if publish_at and expire_at and expire_at <= publish_at:
        return err("expire_at must be after publish_at.", 422, "validation_error")

    ann = Announcement(
        club_id=p.get("club_id"),
        title=title,
        content=content,
        publish_at=publish_at,
        expire_at=expire_at,
        priority=(p.get("priority") or "normal").strip(),
        audience=(p.get("audience") or "all_members").strip(),
        status=status,
        send_email=bool(p.get("send_email")),
        pinned=bool(p.get("pinned")),
    )
    try:
        db.session.add(ann)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return err("Failed to create announcement.", 500, "db_error")
    return ok({"id": ann.id}, 201)

# index for convenience
@api.get("")
def api_root():
    return ok({
        "message": "AI Nexus API",
        "endpoints": [
            "/api/health",
            "/api/dashboard",
            "/api/clubs  [GET, POST] /clubs/<id> [PATCH]",
            "/api/events [GET, POST]",
            "/api/colleges [GET, POST]",
            "/api/coordinators [GET, POST]",
            "/api/announcements [GET, POST]",
        ]
    })
