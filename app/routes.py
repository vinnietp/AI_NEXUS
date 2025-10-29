# routes.py
import os
from datetime import datetime
from operator import or_
from uuid import uuid4

from flask import render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Club, Event ,Coordinator,College,Announcement,Member, member_clubs
from utils import time_ago,parse_dt,card_datetime,table_date,relpath_from_static,clean_phone,clean_role,ALLOWED_ROLES
from sqlalchemy import func, case



def register_routes(app):
    # ---------- Dashboard ----------
    @app.route("/", methods=["GET"])
    def index():
        """Dashboard showing recent activity and statistics."""

        # ✅ Recent (non-deleted) clubs
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))
            .order_by(Club.club_id.desc())
            .limit(2)
            .all()
        )
        recent_clubs = [
            {"name": ch.club_name, "time_ago": time_ago(ch.created_time)}
            for ch in clubs
        ]

        # ✅ Counts for dashboard cards (only active + not deleted)
        active_clubs = (
            db.session.query(func.count(Club.club_id))
            .filter(Club.status == "active", Club.is_deleted.is_(False))
            .scalar()
        )

        active_colleges = (
            db.session.query(func.count(College.college_id))
            .filter(College.status == "active", College.is_deleted.is_(False))
            .scalar()
        )

        active_coordinators = (
            db.session.query(func.count(Coordinator.coordinator_id))
            .filter(Coordinator.status == "active", Coordinator.is_deleted.is_(False))
            .scalar()
        )

        active_members = (
            db.session.query(func.count(Member.member_id))
            .filter(Member.status == "active", Member.is_deleted.is_(False))
            .scalar()
        )

        total_members = (
            db.session.query(func.count(Member.member_id))
            .filter(Member.is_deleted.is_(False))
            .scalar()
        )

        upcoming_events_count = (
            db.session.query(func.count(Event.event_id))
            .filter(Event.status == "upcoming", Event.is_deleted.is_(False))
            .scalar()
        )

        # ✅ Fetch *nearest* upcoming (not deleted) events
        now_local = datetime.now()
        upcoming_events = (
            Event.query
            .filter(
                Event.status == "upcoming",
                Event.start_at >= now_local,
                Event.is_deleted.is_(False)
            )
            .order_by(Event.start_at.asc())  # soonest first
            .limit(2)
            .all()
        )

        upcoming_events_vm = [
            {
                "name": ev.event_name,
                "time_until": time_ago(ev.start_at),
                "description": ev.description or "",
                "start_at": ev.start_at,
            }
            for ev in upcoming_events
        ]

        # ✅ Recent (non-deleted) events for "Recent Activities"
        recent_events = (
            Event.query
            .filter(Event.is_deleted.is_(False))
            .order_by(Event.created_time.desc())
            .limit(2)
            .all()
        )

        recent_events_vm = [
            {"name": ev.event_name, "time_ago": time_ago(ev.created_time)}
            for ev in recent_events
        ]

        # ✅ Clubs dropdown in Event modal (non-deleted)
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))
            .order_by(Club.club_name.asc())
            .all()
        )

        return render_template(
            "index.html",
            recent_clubs=recent_clubs,
            active_clubs=active_clubs,
            active_colleges=active_colleges,
            active_coordinators=active_coordinators,
            active_members=active_members,
            total_members=total_members,
            upcoming_events_count=upcoming_events_count,
            upcoming_events=upcoming_events_vm,
            recent_events=recent_events_vm,
            clubs=clubs,
        )

    # ---------- clubs ----------
    @app.route("/clubs")
    def clubs():
        """Display all active (non-deleted) clubs with coordinator and member info."""

        # ✅ Fetch only non-deleted clubs
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))  # ⬅️ ignore soft-deleted records
            .order_by(Club.created_time.desc())
            .all()
        )

        clubs_vm = []
        for club in clubs:
            # ✅ Coordinator name (if any)
            coordinator_name = club.coordinators[0].coordinator_name if club.coordinators else "—"

            # ✅ Member count (relationship preloaded if using selectinload)
            member_count = len(club.members)

            clubs_vm.append({
                "club_id": club.club_id,
                "club_name": club.club_name,
                "club_category": club.club_category,
                "club_logo": club.club_logo,
                "description": club.description,
                "status": club.status,
                "created_time": club.created_time,
                "members": member_count,
                "coordinator": coordinator_name,
            })

        return render_template("clubs.html", clubs=clubs_vm)

    #create clubs
    @app.route("/clubs/create", methods=["POST"])
    def create_club():
        club_name     = (request.form.get("club_name") or "").strip()
        club_category = (request.form.get("club_category") or "").strip()
        description      = (request.form.get("description") or "").strip()
        status="active"

        def back_to_modal():
            return redirect(url_for("clubs"))

        if not club_name:
            flash("club name is required.", "error")
            return back_to_modal()

        # Check if a non-deleted club with the same name exists (case-insensitive)
        exists = (
            Club.query
            .filter(
                Club.is_deleted.is_(False),
                func.lower(Club.club_name) == club_name.lower()
            )
            .first()
        )
        if exists:
            flash("Club Already exists", "error")
            return back_to_modal()

        # Optional logo upload
        file = request.files.get("club_logo")
        logo_rel_path = None

        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid logo format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return back_to_modal()

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["CLUB_UPLOAD_FOLDER"]  # e.g., <project>/static/uploads/clubs
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)

            logo_rel_path = relpath_from_static(save_path)

        try:
            club = Club(
                club_name=club_name,
                club_category=club_category,
                club_logo=logo_rel_path,
                description=description,
                status=status
            )
            db.session.add(club)
            db.session.commit()
            flash("✅ club created successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create club")
            flash("❌ Failed to create club. Please try again.", "error")
            return back_to_modal()

        return redirect(url_for("clubs"))

    # ---------- Events ----------
    # ---------- Events ----------
    @app.route("/events")
    def events():
        # You’re treating naive datetimes as IST across the app
        now_local = datetime.now()

        # ✅ Only not-deleted, not-cancelled, and in the future
        upcoming_events = (
            Event.query
            .filter(
                Event.is_deleted.is_(False),
                Event.status != "cancelled",
                Event.start_at >= now_local,
            )
            .order_by(Event.start_at.asc())
            .limit(3)
            .all()
        )

        # ✅ All (non-deleted) events for the table/list
        all_events = (
            Event.query
            .filter(Event.is_deleted.is_(False))
            .order_by(Event.created_time.desc())
            .all()
        )

        # ✅ Counts should also ignore soft-deleted rows
        upcoming_count = (
            db.session.query(Event)
            .filter(
                Event.is_deleted.is_(False),
                Event.status == "upcoming",

            )
            .count()
        )

        completed_count = (
            db.session.query(Event)
            .filter(
                Event.is_deleted.is_(False),
                Event.status == "completed",
            )
            .count()
        )

        # ✅ Clubs dropdown should not list deleted clubs
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))
            .order_by(Club.club_name.asc())
            .all()
        )

        return render_template(
            "events.html",
            clubs=clubs,
            upcoming_events=upcoming_events,
            all_events=all_events,
            upcoming_count=upcoming_count,
            completed_count=completed_count,
            card_datetime=card_datetime,
            table_date=table_date,
        )

    # ---------- create events (updated for soft-delete) ----------
    @app.route("/events/create", methods=["POST"])
    def create_event():
        EVENT_STATUS_VALUES = {"upcoming", "completed", "cancelled"}

        def back_to_modal(start_time=None, end_time=None):
            return redirect(url_for("events"))

        f = request.form

        # Required: name
        event_name = (f.get("event_name") or "").strip()
        if not event_name:
            flash("Event name is required.", "error")
            return back_to_modal()

        # Required: club FK exists AND is not soft-deleted
        club_id = f.get("organising_club", type=int)
        club = (
            Club.query
            .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
            .first()
            if club_id else None
        )
        if not club:
            flash("Please select a valid club.", "error")
            return back_to_modal()

        # Status (restricted set)
        status = (f.get("status") or "upcoming").strip().lower()
        if status not in EVENT_STATUS_VALUES:
            flash("Invalid status selected.", "error")
            return back_to_modal()

        # Parse Start/End
        start_date = f.get("start_date")
        start_time = f.get("start_time")
        end_date = f.get("end_date")
        end_time = f.get("end_time")

        # Start is required
        start_at = parse_dt(start_date, start_time)
        if not start_at:
            flash("Please provide valid start date/time.", "error")
            return back_to_modal(start_time, end_time)

        # End is optional — if provided, parse; else None
        end_at = None
        if (end_date or end_time):
            end_at = parse_dt(end_date, end_time) or None
            if end_at and end_at < start_at:
                flash("End time must be after the start time.", "error")
                return back_to_modal(start_time, end_time)

        # Optional fields
        event_coordinator = (f.get("event_coordinator") or "").strip() or None
        venue = (f.get("venue") or "").strip() or None
        description = f.get("description") or ""
        max_participants = f.get("max_participants")
        max_participants = int(max_participants) if (max_participants or "").isdigit() else None

        # Optional image upload
        img_rel_path = None
        file = request.files.get("event_image")
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return back_to_modal(start_time, end_time)

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["EVENT_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)
            img_rel_path = relpath_from_static(save_path)

        # Insert into DB
        try:
            ev = Event(
                event_name=event_name,
                organising_club_id=club.club_id,  # from validated club
                event_coordinator=event_coordinator,
                venue=venue,
                start_at=start_at,
                end_at=end_at,  # may be None
                event_image=img_rel_path,
                max_participants=max_participants,
                status=status,
                description=description,
            )
            db.session.add(ev)
            db.session.commit()
            flash("✅ Event created successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create event")
            flash("❌ Failed to create event. Please try again.", "error")
            return back_to_modal(start_time, end_time)

        return redirect(url_for("events"))

    # ---------- Colleges ----------
    @app.route("/colleges")
    def colleges():
        # 1) List only non-deleted colleges (newest first)
        rows = (
            College.query
            .filter(College.is_deleted.is_(False))
            .order_by(College.created_time.desc(), College.college_id.desc())
            .all()
        )

        # 2) Active member counts per college (exclude soft-deleted members)
        members_by_college = dict(
            db.session.query(Member.college_id, func.count(Member.member_id))
            .filter(
                Member.status == "active",
                Member.is_deleted.is_(False),
            )
            .group_by(Member.college_id)
            .all()
        )

        # 3) Build view model
        colleges_vm = []
        for col in rows:
            colleges_vm.append({
                "college_id": col.college_id,
                "college_name": col.college_name,
                "members_count": members_by_college.get(col.college_id, 0),
                "clubs_count": 0,  # placeholder until wired
                "email": col.email,
                "location": col.location,
                "status": (col.status or "active").lower(),
                "authority_name": col.authority_name,
                "authority_role": col.authority_role,
                "phone": col.phone,
                "description": col.description,
                "created_time": col.created_time,
            })

        # 4) Stats cards (exclude soft-deleted colleges)
        active_count = (
            db.session.query(func.count(College.college_id))
            .filter(College.status == "active", College.is_deleted.is_(False))
            .scalar()
        )
        inactive_count = (
            db.session.query(func.count(College.college_id))
            .filter(College.status == "inactive", College.is_deleted.is_(False))
            .scalar()
        )

        return render_template(
            "colleges.html",
            colleges=colleges_vm,
            active_count=active_count,
            inactive_count=inactive_count,
            q="",
            status="all",
            sort="none",
        )
#create college
    @app.route("/colleges/create", methods=["POST"])
    def create_college():
        def back():
            return redirect(url_for("colleges") + "#collegeModal")

        f = request.form
        name = (f.get("college_name") or "").strip()
        if not name:
            flash("College name is required.", "error")
            return back()

        # ✅ Case-insensitive uniqueness among NON-deleted colleges
        exists = (
            College.query
            .filter(
                College.is_deleted.is_(False),
                func.lower(College.college_name) == name.lower()
            )
            .first()
        )
        if exists:
            flash("A college with this name already exists.", "error")
            return back()

        email = (f.get("email") or "").strip() or None
        location = (f.get("location") or "").strip() or None
        authority = (f.get("authority_name") or "").strip() or None
        role = clean_role(f.get("authority_role"))
        phone = clean_phone(f.get("phone"))
        description = (f.get("description") or "").strip() or None

        try:
            col = College(
                college_name=name,
                authority_name=authority,
                authority_role=role,
                phone=phone,
                description=description,
                email=email,
                location=location,
                status="active",  # force Active on create
                # is_deleted defaults to False; deleted_at stays None
            )
            db.session.add(col)
            db.session.commit()
            flash("✅ College added successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create college")
            flash("❌ Failed to add college. Please try again.", "error")
            return back()

        return redirect(url_for("colleges"))

    # ---------- Coordinators ----------
    @app.route("/coordinators")
    def coordinators():
        """Display active coordinators (non-deleted) along with their clubs and colleges."""

        # ✅ Only non-deleted clubs and colleges (for dropdowns / modal)
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))
            .order_by(Club.club_name.asc())
            .all()
        )
        colleges = (
            College.query
            .filter(College.is_deleted.is_(False))
            .order_by(College.college_name.asc())
            .all()
        )

        # ✅ Stat cards: count active & non-deleted coordinators
        student_count = (
            db.session.query(Coordinator)
            .filter(
                Coordinator.role_type == "student",
                Coordinator.status == "active",
                Coordinator.is_deleted.is_(False),
            )
            .count()
        )

        faculty_count = (
            db.session.query(Coordinator)
            .filter(
                Coordinator.role_type.in_(["faculty", "lead", "co-lead", "mentor"]),
                Coordinator.status == "active",
                Coordinator.is_deleted.is_(False),
            )
            .count()
        )

        # ✅ Fetch only active + non-deleted coordinators and join with non-deleted clubs/colleges
        rows = (
            db.session.query(Coordinator, Club, College)
            .join(Club, Coordinator.club_id == Club.club_id)
            .outerjoin(College, Coordinator.college_id == College.college_id)
            .filter(
                Coordinator.status == "active",
                Coordinator.is_deleted.is_(False),
                Club.is_deleted.is_(False),
                or_(College.is_deleted.is_(False), College.is_deleted.is_(None)),  # handle optional college
            )
            .order_by(Coordinator.created_time.desc())
            .all()
        )

        # ✅ Shape the result for template
        coordinators = []
        for coord, club, college in rows:
            coordinators.append({
                "id": coord.coordinator_id,
                "name": coord.coordinator_name,
                "club": club.club_name if club else "—",
                "club_id": coord.club_id,
                "college_id": coord.college_id,
                "type": coord.role_type or "—",
                "college_or_dept": coord.faculty_dept,
                "faculty_dept": coord.faculty_dept,
                "email": coord.email or "—",
                "phone": coord.phone,
                "image_path": coord.coordinator_image,
                "description": coord.description,
                "status": coord.status,
            })

        return render_template(
            "coordinators.html",
            clubs=clubs,
            colleges=colleges,
            coordinators=coordinators,
            student_count=student_count,
            faculty_count=faculty_count,
        )

    # ---------- create coordinators (updated for soft-delete) ----------
    @app.route("/coordinators/create", methods=["POST"])
    def assign_coordinator():
        f = request.form
        name = (f.get("coordinator_name") or "").strip()
        club_id_raw = f.get("club_id")
        college_raw = f.get("college_id")  # optional
        faculty_dept = (f.get("faculty_dept") or "").strip()
        role_type = (f.get("role_type") or "").strip()
        email = (f.get("email") or "").strip()
        phone = (f.get("phone") or "").strip()
        description = (f.get("description") or "").strip()

        def back_to_modal():
            return redirect(url_for("coordinators") + "#coordinatorModal")

        # --- Basic validation ---
        if not name:
            flash("Coordinator name is required.", "error")
            return back_to_modal()

        # Coerce IDs to int
        try:
            club_id = int(club_id_raw) if club_id_raw else None
        except ValueError:
            club_id = None

        college_id = None
        if college_raw:
            try:
                college_id = int(college_raw)
            except ValueError:
                college_id = None

        if not club_id:
            flash("Club selection is required.", "error")
            return back_to_modal()

        # --- Verify FK targets are NOT soft-deleted ---
        club = (
            Club.query
            .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
            .first()
        )
        if not club:
            flash("Please select a valid (non-deleted) club.", "error")
            return back_to_modal()

        college = None
        if college_id is not None:
            college = (
                College.query
                .filter(College.college_id == college_id, College.is_deleted.is_(False))
                .first()
            )
            if not college:
                flash("Selected college is invalid or deleted.", "error")
                return back_to_modal()

        # --- Optional image upload ---
        file = request.files.get("coordinator_image")
        image_rel_path = None
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return back_to_modal()

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["COORDINATOR_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)

            image_rel_path = os.path.relpath(save_path, current_app.static_folder)

        # --- Insert ---
        try:
            coordinator = Coordinator(
                coordinator_name=name,
                club_id=club_id,
                college_id=college_id,
                faculty_dept=faculty_dept,
                role_type=role_type,
                email=email,
                phone=phone,
                coordinator_image=image_rel_path,
                description=description,
                status="active",  # default active
                # is_deleted defaults to False
            )
            db.session.add(coordinator)
            db.session.commit()
            flash("✅ Coordinator assigned successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create coordinator")
            flash("❌ Failed to assign coordinator. Please try again.", "error")
            return back_to_modal()

        return redirect(url_for("coordinators"))

    from sqlalchemy import or_

    # ---------- Announcements ----------
    @app.route("/announcements")
    def announcements():
        # Handle query parameters
        q = request.args.get('q', '').strip()
        status_filter = request.args.get('status', 'all')
        club_id = request.args.get('club_id', type=int) if request.args.get('club_id') else None
        sort_by = request.args.get('sort', 'none')

        # ✅ Only non-deleted clubs in dropdown
        clubs = (
            Club.query
            .filter(Club.is_deleted.is_(False))
            .order_by(Club.club_name.asc())
            .all()
        )

        # Base query with join for club
        base_query = (
            db.session.query(Announcement)
            .outerjoin(Club, Announcement.club_id == Club.club_id)
            # ✅ Only non-deleted announcements, and if linked to a club, that club must not be deleted
            .filter(
                Announcement.is_deleted.is_(False),
                or_(Announcement.club_id.is_(None), Club.is_deleted.is_(False))
            )
        )

        # Apply filters
        if q:
            base_query = base_query.filter(
                Announcement.title.ilike(f'%{q}%') | Announcement.content.ilike(f'%{q}%')
            )

        if status_filter != 'all':
            base_query = base_query.filter(Announcement.status == status_filter)

        if club_id:
            # ✅ Only show announcements for a non-deleted club
            base_query = base_query.filter(
                Announcement.club_id == club_id,
                Club.is_deleted.is_(False),
            )

        # Apply sorting
        if sort_by == 'title':
            qry = base_query.order_by(Announcement.title.asc())
        elif sort_by == 'club':
            qry = base_query.order_by(Club.club_name.asc())
        elif sort_by == 'newest':
            qry = base_query.order_by(Announcement.updated_at.desc())
        elif sort_by == 'oldest':
            qry = base_query.order_by(Announcement.updated_at.asc())
        else:
            qry = base_query.order_by(Announcement.pinned.desc(), Announcement.updated_at.desc())

        announcements = qry.all()

        return render_template(
            "announcements.html",
            clubs=clubs,
            announcements=announcements,
            q=q,
            club_id=club_id,
            status=status_filter,
            sort=sort_by,
        )

   ## ---------- create announcements (updated for soft-delete) ----------
    @app.route("/announcements/create", methods=["POST"])
    def create_announcement():
        # --- Fields ---
        f = request.form
        title = (f.get("title") or "").strip()
        content = (f.get("content") or "").strip()

        club_id = None
        club_id_raw = f.get("club_id")
        if club_id_raw:
            try:
                club_id = int(club_id_raw)
            except ValueError:
                club_id = None

        publish_date = f.get("publish_date")
        publish_time = f.get("publish_time")
        expire_date = f.get("expire_date")
        expire_time = f.get("expire_time")

        priority = (f.get("priority") or "normal").strip()
        audience = (f.get("audience") or "all_members").strip()
        status = (f.get("status") or "draft").strip().lower()  # draft | published
        send_email = f.get("send_email") is not None
        pinned = f.get("pinned") is not None

        def back_to_modal():
            return redirect(url_for("announcements"))

        # --- Basic validation (pre-parse) ---
        errors = []
        if not title:
            errors.append("Title is required.")
        if not content:
            errors.append("Content is required.")
        if status not in {"draft", "published"}:
            errors.append("Invalid status.")
        if status == "published" and not publish_date:
            errors.append("Publish date & time is required to publish.")

        # ✅ If a club is selected, ensure it exists and is NOT soft-deleted
        club = None
        if club_id is not None:
            club = (
                Club.query
                .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
                .first()
            )
            if not club:
                errors.append("Please select a valid (non-deleted) club.")

        if errors:
            for e in errors:
                flash(e, "error")
            return back_to_modal()

        # --- Parse datetimes ---
        publish_at = parse_dt(publish_date, publish_time) if publish_date else None
        expire_at = parse_dt(expire_date, expire_time) if expire_date else None

        # --- Cross-field validation (post-parse) ---
        if publish_at and expire_at and expire_at <= publish_at:
            flash("Expiration must be after publish time.", "error")
            return back_to_modal()
        if status == "published" and not publish_at:
            flash("Publish date & time is required to publish.", "error")
            return back_to_modal()

        # --- Save ---
        try:
            ann = Announcement(
                club_id=club.club_id if club else None,
                title=title,
                content=content,
                publish_at=publish_at,
                expire_at=expire_at,
                priority=priority,
                audience=audience,
                status=status,  # draft | published
                send_email=send_email,
                pinned=pinned,
                # is_deleted defaults to False
            )
            db.session.add(ann)
            db.session.commit()
            flash("Announcement saved." if status == "draft" else "Announcement published.", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create announcement")
            flash("Failed to create announcement. Please try again.", "error")
            return back_to_modal()

        return redirect(url_for("announcements"))

    ################################################################################################
#EDIT OPERATIONS
    from sqlalchemy import func

    @app.route("/clubs/update", methods=["POST"])
    def update_club():
        f = request.form
        club_id = f.get("club_id", type=int)
        club = Club.query.get(club_id)

        # ✅ Check if club exists and is not deleted
        if not club or getattr(club, "is_deleted", False):
            flash("❌ Club not found or has been deleted.", "error")
            return redirect(url_for("clubs"))

        # ✅ Update basic fields
        club.club_name = (f.get("club_name") or "").strip() or club.club_name
        club.club_category = (f.get("club_category") or "").strip() or None
        club.description = (f.get("description") or "").strip() or None

        # ✅ Handle status safely
        status = (f.get("status") or "").strip().lower()
        if status in ("active", "inactive"):
            club.status = status

        # ✅ Handle coordinator_id (ignore if coordinator is soft-deleted)
        coordinator_id_raw = f.get("coordinator_id")
        if coordinator_id_raw:
            coordinator_id = int(coordinator_id_raw)
            coordinator = (
                Coordinator.query
                .filter(
                    Coordinator.coordinator_id == coordinator_id,
                    Coordinator.is_deleted.is_(False)
                )
                .first()
            )
            if not coordinator:
                flash("Invalid or deleted coordinator selected.", "error")
                return redirect(url_for("clubs"))
            club.coordinator_id = coordinator_id
        else:
            club.coordinator_id = None

        # ✅ Optional logo upload
        file = request.files.get("club_logo")
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext in allowed_ext:
                safe_name = secure_filename(file.filename)
                save_dir = current_app.config["CLUB_UPLOAD_FOLDER"]
                os.makedirs(save_dir, exist_ok=True)
                path = os.path.join(save_dir, safe_name)
                file.save(path)
                rel = os.path.relpath(path, current_app.static_folder).replace("\\", "/")
                club.club_logo = rel
            else:
                flash("Invalid logo format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return redirect(url_for("clubs"))

        # ✅ Commit update
        try:
            db.session.commit()
            flash("✅ Club updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update club")
            flash("❌ Failed to update club.", "error")

        # ✅ Refresh the page so changes reflect immediately
        return redirect(url_for("clubs"))

    #UPDATE EVENTS
    EVENT_STATUS_VALUES = {"upcoming", "completed", "cancelled"}
    ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

    @app.route("/events/update", methods=["POST"])
    def update_event():
        f = request.form
        event_id = f.get("event_id", type=int)
        ev = db.session.get(Event, event_id)

        # ✅ must exist and not be soft-deleted
        if not ev or getattr(ev, "is_deleted", False):
            flash("Event not found or has been deleted.", "error")
            return redirect(url_for("events"))

        # ✅ Validate club: must exist and not be soft-deleted
        club_id = f.get("organising_club", type=int)
        club = (
            Club.query
            .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
            .first()
            if club_id else None
        )
        if not club:
            flash("Please select a valid club.", "error")
            return redirect(url_for("events"))

        # Status (only allow known values)
        status = (f.get("status") or "upcoming").strip().lower()
        if status not in EVENT_STATUS_VALUES:
            flash("Invalid status selected.", "error")
            return redirect(url_for("events"))

        # Required name
        name = (f.get("event_name") or "").strip()
        if not name:
            flash("Event name is required.", "error")
            return redirect(url_for("events"))

        # ---- Parse datetimes ----
        start_date = (f.get("start_date") or "").strip()
        start_time = (f.get("start_time") or "").strip()
        end_date = (f.get("end_date") or "").strip()
        end_time = (f.get("end_time") or "").strip()

        new_start_at = parse_dt(start_date, start_time) if (start_date or start_time) else ev.start_at
        new_end_at = parse_dt(end_date, end_time) if (end_date or end_time) else ev.end_at

        if not new_start_at:
            flash("Please provide a valid start date/time.", "error")
            return redirect(url_for("events"))

        if new_end_at and new_end_at < new_start_at:
            flash("End time cannot be before start time.", "error")
            return redirect(url_for("events"))

        if status == "upcoming":
            from datetime import datetime
            now = datetime.now(new_start_at.tzinfo) if getattr(new_start_at, "tzinfo", None) else datetime.now()
            if new_start_at < now:
                flash("Start time must be in the future for upcoming events.", "error")
                return redirect(url_for("events"))

        # ---- Assign fields ----
        ev.event_name = name
        ev.organising_club_id = club.club_id
        ev.event_coordinator = (f.get("event_coordinator") or "").strip() or None
        ev.venue = (f.get("venue") or "").strip() or None
        ev.start_at = new_start_at
        ev.end_at = new_end_at
        ev.description = f.get("description") or ""
        ev.status = status

        max_participants_raw = (f.get("max_participants") or "").strip()
        ev.max_participants = int(max_participants_raw) if max_participants_raw.isdigit() else None

        # ---- Optional image upload ----
        file = request.files.get("event_image")
        if file and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in ALLOWED_IMAGE_EXT:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return redirect(url_for("events"))

            base = secure_filename(file.filename.rsplit(".", 1)[0])[:60] or "event"
            unique_name = f"{base}-{uuid4().hex[:10]}.{ext}"
            save_dir = current_app.config["EVENT_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, unique_name)
            try:
                file.save(save_path)
            except Exception:
                current_app.logger.exception("Failed to save event image")
                flash("Failed to save the image. Please try again.", "error")
                return redirect(url_for("events"))
            ev.event_image = relpath_from_static(save_path)

        try:
            db.session.commit()
            flash("✅ Event updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update event")
            flash("❌ Failed to update event.", "error")

        return redirect(url_for("events"))

   #Edit colleges
    @app.route("/colleges/update", methods=["POST"])
    def update_college():
        f = request.form
        college_id = f.get("college_id", type=int)
        col = College.query.get(college_id)

        # ✅ Must exist and not be soft-deleted
        if not col or getattr(col, "is_deleted", False):
            flash("College not found or has been deleted.", "error")
            return redirect(url_for("colleges"))

        # Required name
        name = (f.get("college_name") or "").strip()
        if not name:
            flash("College name is required.", "error")
            return redirect(url_for("colleges"))

        # ✅ Ensure unique name among NON-deleted colleges (exclude self)
        exists = (
            College.query
            .filter(
                College.is_deleted.is_(False),
                func.lower(College.college_name) == name.lower(),
                College.college_id != college_id,
            )
            .first()
        )
        if exists:
            flash("Another college with this name already exists.", "error")
            return redirect(url_for("colleges"))

        # Optional fields
        email = (f.get("email") or "").strip() or None
        location = (f.get("location") or "").strip() or None
        authority = (f.get("authority_name") or "").strip() or None
        role = (f.get("authority_role") or "").strip() or None
        phone = (f.get("phone") or "").strip() or None
        description = (f.get("description") or "").strip() or None
        status = (f.get("status") or "").strip().lower()
        if status not in ("active", "inactive"):
            status = "active"

        # Apply updates
        col.college_name = name
        col.email = email
        col.location = location
        col.authority_name = authority
        col.authority_role = role
        col.phone = phone
        col.description = description
        col.status = status

        try:
            db.session.commit()
            flash("✅ College updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update college")
            flash("❌ Failed to update college.", "error")

        return redirect(url_for("colleges"))

    #Edit coordinators
    @app.route("/coordinators/update", methods=["POST"])
    def update_coordinator():
        f = request.form
        cid = f.get("coordinator_id", type=int)
        co = Coordinator.query.get(cid)

        # ✅ Must exist and not be soft-deleted
        if not co or getattr(co, "is_deleted", False):
            flash("Coordinator not found or has been deleted.", "error")
            return redirect(url_for("coordinators"))

        # Required: name
        name = (f.get("coordinator_name") or "").strip()
        if not name:
            flash("Coordinator name is required.", "error")
            return redirect(url_for("coordinators"))

        # ✅ Required: club must exist and NOT be soft-deleted
        club_id = f.get("club_id", type=int)
        club = (
            Club.query
            .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
            .first()
            if club_id else None
        )
        if not club:
            flash("Please select a valid (non-deleted) club.", "error")
            return redirect(url_for("coordinators"))

        # ✅ Optional college: if provided, must NOT be soft-deleted
        college_id = None
        college_id_raw = f.get("college_id")
        if college_id_raw:
            try:
                college_id = int(college_id_raw)
            except ValueError:
                college_id = None

        if college_id is not None:
            college = (
                College.query
                .filter(College.college_id == college_id, College.is_deleted.is_(False))
                .first()
            )
            if not college:
                flash("Selected college is invalid or deleted.", "error")
                return redirect(url_for("coordinators"))

        # Assign fields
        co.coordinator_name = name
        co.club_id = club.club_id
        co.college_id = college_id
        co.faculty_dept = (f.get("faculty_dept") or "").strip() or None
        co.role_type = (f.get("role_type") or "").strip() or None
        co.email = (f.get("email") or "").strip() or None
        co.phone = (f.get("phone") or "").strip() or None
        co.description = (f.get("description") or "").strip() or None

        # Status (guarded)
        status = (f.get("status") or co.status or "active").strip().lower()
        if status not in ("active", "inactive"):
            status = "active"
        co.status = status

        # Optional image upload
        file = request.files.get("coordinator_image")
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return redirect(url_for("coordinators"))

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["COORDINATOR_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)

            rel = os.path.relpath(save_path, current_app.static_folder).replace("\\", "/")
            co.coordinator_image = rel

        try:
            db.session.commit()
            flash("✅ Coordinator updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update coordinator")
            flash("❌ Failed to update coordinator.", "error")

        return redirect(url_for("coordinators"))

    #Edit announcements
    from sqlalchemy import or_

    # ---------- Edit announcements (soft-delete safe) ----------
    @app.route("/announcements/update", methods=["POST"])
    def update_announcement():
        f = request.form
        ann_id = f.get("id", type=int)
        ann = Announcement.query.get(ann_id)

        # ✅ Must exist and not be soft-deleted
        if not ann or getattr(ann, "is_deleted", False):
            flash("Announcement not found or has been deleted.", "error")
            return redirect(url_for("announcements"))

        # Required fields
        title = (f.get("title") or "").strip()
        content = (f.get("content") or "").strip()
        if not title or not content:
            flash("Title and content are required.", "error")
            return redirect(url_for("announcements"))

        # Optional club (must be non-deleted if provided)
        club_id = None
        club_id_raw = f.get("club_id")
        if club_id_raw:
            try:
                club_id = int(club_id_raw)
            except ValueError:
                club_id = None

        club = None
        if club_id is not None:
            club = (
                Club.query
                .filter(Club.club_id == club_id, Club.is_deleted.is_(False))
                .first()
            )
            if not club:
                flash("Please select a valid (non-deleted) club.", "error")
                return redirect(url_for("announcements"))

        # Parse datetimes
        publish_date = f.get("publish_date")
        publish_time = f.get("publish_time")
        expire_date = f.get("expire_date")
        expire_time = f.get("expire_time")

        publish_at = parse_dt(publish_date, publish_time) if publish_date else None
        expire_at = parse_dt(expire_date, expire_time) if expire_date else None

        # Cross-field validation
        status = (f.get("status") or "draft").strip().lower()
        if status not in {"draft", "published"}:
            flash("Invalid status.", "error")
            return redirect(url_for("announcements"))
        if status == "published" and not publish_at:
            flash("Publish date & time is required to publish.", "error")
            return redirect(url_for("announcements"))
        if publish_at and expire_at and expire_at <= publish_at:
            flash("Expiration must be after publish time.", "error")
            return redirect(url_for("announcements"))

        # Normalizations
        priority = (f.get("priority") or "normal").strip().lower()
        if priority not in {"normal", "high", "urgent"}:
            priority = "normal"
        audience = (f.get("audience") or "all_members").strip().lower()
        pinned = f.get("pinned") is not None
        send_email = f.get("send_email") is not None

        # Apply
        ann.title = title
        ann.content = content
        ann.club_id = club.club_id if club else None
        ann.publish_at = publish_at
        ann.expire_at = expire_at
        ann.priority = priority
        ann.audience = audience
        ann.status = status
        ann.pinned = pinned
        ann.send_email = send_email

        try:
            db.session.commit()
            flash("✅ Announcement updated.", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update announcement")
            flash("❌ Failed to update announcement.", "error")

        return redirect(url_for("announcements"))

    # ---------- DELETE OPERATIONS (SOFT DELETE) ----------

    @app.route("/clubs/delete", methods=["POST"])
    def delete_club_form():
        """Soft delete a club from the admin UI (mark is_deleted=True)."""
        club_id = request.form.get("club_id", type=int)
        club = Club.query.get(club_id)

        if not club:
            flash("❌ Club not found.", "error")
            return redirect(url_for("clubs"))

        try:
            club.is_deleted = True
            club.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ Club moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete club")
            flash("❌ Failed to delete club.", "error")

        return redirect(url_for("clubs"))

    @app.route("/events/delete", methods=["POST"])
    def delete_event_form():
        """Soft delete an event from the admin UI."""
        event_id = request.form.get("event_id", type=int)
        event = Event.query.get(event_id)

        if not event:
            flash("❌ Event not found.", "error")
            return redirect(url_for("events"))

        try:
            event.is_deleted = True
            event.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ Event moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete event")
            flash("❌ Failed to delete event.", "error")

        return redirect(url_for("events"))

    @app.route("/colleges/delete", methods=["POST"])
    def delete_college_form():
        """Soft delete a college from the admin UI."""
        college_id = request.form.get("college_id", type=int)
        college = College.query.get(college_id)

        if not college:
            flash("❌ College not found.", "error")
            return redirect(url_for("colleges"))

        try:
            college.is_deleted = True
            college.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ College moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete college")
            flash("❌ Failed to delete college.", "error")

        return redirect(url_for("colleges"))

    @app.route("/coordinators/delete", methods=["POST"])
    def delete_coordinator_form():
        """Soft delete a coordinator from the admin UI."""
        coordinator_id = request.form.get("coordinator_id", type=int)
        coordinator = Coordinator.query.get(coordinator_id)

        if not coordinator:
            flash("❌ Coordinator not found.", "error")
            return redirect(url_for("coordinators"))

        try:
            coordinator.is_deleted = True
            coordinator.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ Coordinator moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete coordinator")
            flash("❌ Failed to delete coordinator.", "error")

        return redirect(url_for("coordinators"))

    @app.route("/announcements/delete", methods=["POST"])
    def delete_announcement_form():
        """Soft delete an announcement from the admin UI."""
        announcement_id = request.form.get("announcement_id", type=int)
        announcement = Announcement.query.get(announcement_id)

        if not announcement:
            flash("❌ Announcement not found.", "error")
            return redirect(url_for("announcements"))

        try:
            announcement.is_deleted = True
            announcement.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ Announcement moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete announcement")
            flash("❌ Failed to delete announcement.", "error")

        return redirect(url_for("announcements"))

        # ---------- Members ----------
    @app.route("/members")
    def members():
            # Handle query parameters
            q = request.args.get('q', '').strip()
            club_ids = request.args.getlist('club_ids')
            status_filter = request.args.get('status', 'all')
            sort_by = request.args.get('sort', 'none')

            # ✅ Dropdown data: only non-deleted clubs/colleges
            clubs = (
                Club.query
                .filter(Club.is_deleted.is_(False))
                .order_by(Club.club_name.asc())
                .all()
            )
            colleges = (
                College.query
                .filter(College.is_deleted.is_(False))
                .order_by(College.college_name.asc())
                .all()
            )

            # ✅ Base query: only non-deleted members; keep outer-join to college
            query = (
                db.session.query(Member, College)
                .outerjoin(College, Member.college_id == College.college_id)
                .filter(Member.is_deleted.is_(False))
            )

            # Apply search filter
            if q:
                query = query.filter(Member.member_name.ilike(f'%{q}%'))

            # Apply club filter (ensure clubs are non-deleted)
            club_ids = request.args.getlist('club_ids')
            club_ids = [int(cid) for cid in club_ids if cid.isdigit()]
            if club_ids:
                query = (
                    query
                    .join(member_clubs, Member.member_id == member_clubs.c.member_id)
                    .join(Club, member_clubs.c.club_id == Club.club_id)
                    .filter(Club.is_deleted.is_(False), member_clubs.c.club_id.in_(club_ids))
                )

            # Apply status filter (on non-deleted members)
            if status_filter == 'active':
                query = query.filter((func.lower(Member.status) == 'active') | (Member.status.is_(None)))
            elif status_filter == 'inactive':
                query = query.filter(func.lower(Member.status) == 'inactive')

            # Apply sorting
            if sort_by == 'name':
                query = query.order_by(Member.member_name.asc())
            elif sort_by == 'club':
                # order by the alphabetically first non-deleted club name of each member
                query = (
                    query
                    .outerjoin(Member.clubs)  # joins Club via relationship
                    .filter(or_(Club.is_deleted.is_(False), Club.club_id.is_(None)))
                    .group_by(Member, College)
                    .order_by(func.min(Club.club_name).asc())
                )
            elif sort_by == 'college':
                # keep members even if their college is deleted/None; deleted colleges will sort as NULL
                query = query.order_by(College.college_name.asc())
            elif sort_by == 'email':
                query = query.order_by(Member.email.asc())
            elif sort_by == 'newest':
                query = query.order_by(Member.created_time.desc())
            elif sort_by == 'oldest':
                query = query.order_by(Member.created_time.asc())
            else:
                query = query.order_by(Member.created_time.desc())

            rows = query.all()

            # Shape data for the template
            members = []
            for mem, college in rows:
                # ✅ Only show non-deleted clubs in the list
                visible_clubs = [c for c in mem.clubs if not getattr(c, "is_deleted", False)]
                club_names = [c.club_name for c in visible_clubs]
                club_str = ', '.join(club_names) if club_names else "—"

                college_name = (
                    college.college_name if (college and not getattr(college, "is_deleted", False)) else "—")

                members.append({
                    "id": mem.member_id,
                    "name": mem.member_name,
                    "club": club_str,
                    "college": college_name,
                    "college_id": mem.college_id,
                    "faculty_dept": mem.faculty_dept,
                    "email": mem.email,
                    "phone": mem.phone,
                    "image_path": mem.member_image,
                    "description": mem.description,
                    "status": mem.status,
                    "club_ids": [c.club_id for c in visible_clubs],
                    "created_time": mem.created_time
                })

            # ✅ Counts for stats (exclude soft-deleted members)
            total_members = (
                    db.session.query(func.count(Member.member_id))
                    .filter(Member.is_deleted.is_(False))
                    .scalar() or 0
            )
            active_members = (
                    db.session.query(func.count(Member.member_id))
                    .filter(
                        Member.is_deleted.is_(False),
                        (Member.status == "active") | (Member.status.is_(None))
                    )
                    .scalar() or 0
            )
            inactive_members = total_members - active_members

            return render_template(
                "members.html",
                clubs=clubs,
                colleges=colleges,
                members=members,
                total_members=total_members,
                active_members=active_members,
                inactive_members=inactive_members,
                q=q,
                club_ids=club_ids,
                status=status_filter,
                sort=sort_by,
            )

    # ---------- Members: create (updated for soft-delete) ----------
    @app.route("/members/create", methods=["POST"])
    def create_member():
        name = (request.form.get("member_name") or "").strip()
        raw_ids = request.form.getlist("club_ids")  # e.g., ['3','5','5']
        club_ids = sorted({int(x) for x in raw_ids if str(x).isdigit()})

        college_raw = request.form.get("college_id")
        college_id = int(college_raw) if college_raw and str(college_raw).isdigit() else None

        faculty_dept = (request.form.get("faculty_dept") or "").strip() or None
        email = (request.form.get("email") or "").strip() or None
        phone = (request.form.get("phone") or "").strip() or None
        description = (request.form.get("description") or "").strip() or None

        def back_to_modal():
            return redirect(url_for("members") + "#memberModal")

        # --- Validation ---
        if not name:
            flash("Member name is required.", "error")
            return back_to_modal()
        if not club_ids:
            flash("At least one club selection is required.", "error")
            return back_to_modal()

        # ✅ Fetch & validate clubs: must exist AND not be soft-deleted
        clubs = (
            Club.query
            .filter(Club.club_id.in_(club_ids), Club.is_deleted.is_(False))
            .all()
        )
        if len(clubs) != len(club_ids):
            flash("Invalid club selection (one or more clubs are deleted or missing).", "error")
            return back_to_modal()

        # ✅ Validate college if provided: must not be soft-deleted
        if college_id is not None:
            college = (
                College.query
                .filter(College.college_id == college_id, College.is_deleted.is_(False))
                .first()
            )
            if not college:
                flash("Selected college is invalid or deleted.", "error")
                return back_to_modal()

        # --- Optional image upload ---
        file = request.files.get("member_image")
        image_rel_path = None
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return back_to_modal()

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["MEMBER_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)
            image_rel_path = relpath_from_static(save_path)

        # --- Insert into DB ---
        try:
            member = Member(
                member_name=name,
                college_id=college_id,
                faculty_dept=faculty_dept,
                email=email,
                phone=phone,
                member_image=image_rel_path,
                description=description,
                status="active",  # is_deleted defaults to False
            )
            member.clubs = clubs  # attach many clubs at once
            db.session.add(member)
            db.session.commit()
            flash("✅ Member added successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to create member")
            flash("❌ Failed to add member. Please try again.", "error")
            return back_to_modal()

        return redirect(url_for("members"))

        # Edit members
    @app.route("/members/update", methods=["POST"])
    def update_member():
        f = request.form
        mid = f.get("member_id", type=int)
        me = Member.query.get(mid)
        if not me:
            flash("Member not found.", "error")
            return redirect(url_for("members"))

        # Required: name and clubs
        name = (f.get("member_name") or "").strip()
        club_ids = request.form.getlist("club_ids")
        if not name:
            flash("Member name is required.", "error")
            return redirect(url_for("members"))
        if not club_ids:
            flash("At least one club selection is required.", "error")
            return redirect(url_for("members"))

        # Validate club_ids exist
        clubs = Club.query.filter(Club.club_id.in_(club_ids)).all()
        if len(clubs) != len(club_ids):
            flash("Invalid club selection.", "error")
            return redirect(url_for("members"))

        # Optional: college
        college_id_raw = f.get("college_id")
        college_id = int(college_id_raw) if college_id_raw else None

        # Assign fields
        me.member_name = name
        me.college_id = college_id
        me.faculty_dept = (f.get("faculty_dept") or "").strip() or None
        me.email = (f.get("email") or "").strip() or None
        me.phone = (f.get("phone") or "").strip() or None
        me.description = (f.get("description") or "").strip() or None

        # Optional: status select in edit (default/guard)
        status = (f.get("status") or me.status or "active").strip().lower()
        if status not in ("active", "inactive"):
            status = "active"
        me.status = status

        # Update clubs relationship
        me.clubs = clubs

        # Optional image upload (same pattern as your create route)
        file = request.files.get("member_image")
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return redirect(url_for("members"))

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["MEMBER_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)

            rel = os.path.relpath(save_path, current_app.static_folder).replace("\\", "/")
            me.member_image = rel

        try:
            db.session.commit()
            flash("✅ Member updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update member")
            flash("❌ Failed to update member.", "error")

        return redirect(url_for("members"))

    #Delete Member
    @app.route("/members/delete", methods=["POST"])
    def delete_member_form():
        """Soft-delete a member from the admin UI (mark is_deleted = True)."""
        member_id = request.form.get("member_id", type=int)
        member = Member.query.get(member_id)

        if not member:
            flash("❌ Member not found.", "error")
            return redirect(url_for("members"))

        try:
            # Soft delete
            member.is_deleted = True
            member.deleted_at = func.now()
            db.session.commit()
            flash("🗑️ Member moved to trash (soft deleted).", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to soft delete member")
            flash("❌ Failed to delete member.", "error")

        return redirect(url_for("members"))
