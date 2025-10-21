# routes.py
import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Club, Event ,Coordinator,College,Announcement
from utils import time_ago,parse_dt,card_datetime,table_date,relpath_from_static,clean_phone,clean_role,ALLOWED_ROLES
from sqlalchemy import func


def register_routes(app):
    # ---------- Dashboard ----------
    @app.route("/", methods=["GET"])
    def index():
        # Recent clubs
        clubs = Club.query.order_by(Club.club_id.desc()).limit(2).all()
        recent_clubs = [
            {"name": ch.club_name, "time_ago": time_ago(ch.created_time)}
            for ch in clubs
        ]
        # Counts for dashboard cards
        active_clubs = db.session.query(func.count(Club.club_id)) \
            .filter(Club.status == "active").scalar()

        active_colleges = db.session.query(func.count(College.college_id)) \
            .filter(College.status == "active").scalar()

        active_coordinators = db.session.query(func.count(Coordinator.coordinator_id)) \
            .filter(Coordinator.status == "active").scalar()

        upcoming_events_count = db.session.query(func.count(Event.event_id)) \
            .filter(Event.status == "upcoming").scalar()

        # ✅ Fetch *nearest* upcoming events (sorted by how soon they start)
        now_local = datetime.now()
        upcoming_events = (
            Event.query
            .filter(Event.status == "upcoming", Event.start_at >= now_local)
            .order_by(Event.start_at.asc())  # soonest first
            .limit(2)
            .all()
        )

        upcoming_events_vm = [
            {
                "name": ev.event_name,
                "time_until": time_ago(ev.start_at),  # ⬅️ reuse the same helper
                "description": ev.description or "",
                "start_at": ev.start_at
            }
            for ev in upcoming_events
        ]
        # Recent events for "Recent Activities" (latest 2 by creation time)
        recent_events = (
            Event.query
            .order_by(Event.created_time.desc())  # if your column is created_time
            .limit(2)
            .all()
        )
        recent_events_vm = [
            {
                "name": ev.event_name,
                "time_ago": time_ago(ev.created_time),  # e.g. "5 hours ago"
            }
            for ev in recent_events
        ]
        return render_template(
            "index.html",
            recent_clubs=recent_clubs,
            active_clubs=active_clubs,
            active_colleges=active_colleges,
            active_coordinators=active_coordinators,
            upcoming_events_count=upcoming_events_count,
            upcoming_events=upcoming_events_vm,
            recent_events=recent_events_vm # 👈 send to template
        )

    # ---------- clubs ----------
    @app.route("/clubs")
    def clubs():
        clubs = Club.query.order_by(Club.club_name.asc()).all()
        return render_template("clubs.html", clubs=clubs)

    #create clubs
    @app.route("/clubs/create", methods=["POST"])
    def create_club():
        club_name     = (request.form.get("club_name") or "").strip()
        club_category = (request.form.get("club_category") or "").strip()
        coordinator      = (request.form.get("coordinator") or "").strip()
        coordinator_type = (request.form.get("coordinator_type") or "").strip()
        description      = (request.form.get("description") or "").strip()
        status="active"

        def back_to_modal():
            return redirect(url_for("index") + "#clubModal")

        if not club_name:
            flash("club name is required.", "error")
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
                coordinator=coordinator,
                coordinator_type=coordinator_type,
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
    @app.route("/events")
    def events():
        # You’re treating naive datetimes as IST across the app
        now_local = datetime.now()
        upcoming_events = (
            Event.query
            .filter(Event.status != "cancelled", Event.start_at >= now_local)
            .order_by(Event.start_at.asc())
            .limit(3)
            .all()
        )

        all_events = (
            Event.query
            .order_by(Event.start_at.desc())
            .all()
        )

        upcoming_count = (
            db.session.query(Event)
            .filter(Event.status != "cancelled", Event.start_at >= now_local)
            .count()
        )
        completed_count = (
            db.session.query(Event)
            .filter(Event.status == "completed")
            .count()
        )

        clubs = Club.query.order_by(Club.club_name.asc()).all()  # for modal dropdown

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

    #create events
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

        # Required: club FK exists
        club_id = f.get("organising_club", type=int)
        if not club_id or not Club.query.get(club_id):
            flash("Please select a valid club.", "error")
            return back_to_modal()

        # Status (restricted set)
        status = (f.get("status") or "upcoming").strip().lower()
        if status not in EVENT_STATUS_VALUES:
            flash("Invalid status selected.", "error")
            return back_to_modal()

        # NEW: parse Start/End from date + single 24h HH:MM (30-min steps)
        start_date = f.get("start_date")
        end_date = f.get("end_date")
        start_time = f.get("start_time")  # "HH:MM"
        end_time = f.get("end_time")  # "HH:MM"

        # Reuse your announcements helper
        start_at = parse_dt(start_date, start_time)  # naive local datetime (IST by convention)
        end_at = parse_dt(end_date, end_time)

        if not start_at or not end_at:
            flash("Please provide valid start and end date/time.", "error")
            return back_to_modal(start_time, end_time)

        if end_at <= start_at:
            flash("End time must be after start time.", "error")
            return back_to_modal(start_time, end_time)

        # Optional fields
        event_coordinator = (f.get("event_coordinator") or "").strip() or None
        venue = (f.get("venue") or "").strip() or None
        description = f.get("description") or ""
        max_participants = f.get("max_participants")
        max_participants = int(max_participants) if max_participants and max_participants.isdigit() else None

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
            save_dir = current_app.config["EVENT_UPLOAD_FOLDER"]  # e.g., <project>/static/uploads/events
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)
            img_rel_path = relpath_from_static(save_path)

        # Insert into DB
        try:
            ev = Event(
                event_name=event_name,
                organising_club_id=club_id,
                event_coordinator=event_coordinator,
                venue=venue,
                start_at=start_at,
                end_at=end_at,
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
        rows = College.query.order_by(College.college_name.asc()).all()

        # If your template doesn’t need the new fields yet, you can keep VM minimal.
        colleges_vm = []
        for col in rows:
            colleges_vm.append({
                "college_id": col.college_id,
                "college_name": col.college_name,
                "members_count": 0,  # placeholder until you track members
                "clubs_count": 0,  # fill from relationship later if needed
                "email": col.email,
                "location": col.location,
                "status": (col.status or "active").lower(),
                # You can pass these too if/when you render them:
                "authority_name": col.authority_name,
                "authority_role": col.authority_role,
                "phone": col.phone,
                "description": col.description,
            })

        active_count = sum(1 for r in rows if (r.status or "active").lower() == "active")
        inactive_count = len(rows) - active_count

        return render_template("colleges.html",
                               colleges=colleges_vm,
                               active_count=active_count,
                               inactive_count=inactive_count)

    @app.route("/colleges/create", methods=["POST"])
    def create_college():
        def back():
            return redirect(url_for("colleges") + "#collegeModal")

        f = request.form
        name = (f.get("college_name") or "").strip()
        if not name:
            flash("College name is required.", "error")
            return back()

        # Case-insensitive uniqueness (exact match)
        exists = College.query.filter(func.lower(College.college_name) == name.lower()).first()
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
                status="active",  # ← force Active on create
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
        """
        Show coordinators management page.
        - Pass clubs for the modal dropdown
        - Pass colleges for the modal select
        - Pass ONLY ACTIVE coordinators for the table (with club & college/department info)
        - Compute simple counts for the stat cards
        """
        # Dropdown data
        clubs = Club.query.order_by(Club.club_name.asc()).all()
        colleges = College.query.order_by(College.college_name.asc()).all()

        # Stat cards (active only)
        student_count = (
            db.session.query(Coordinator)
            .filter(Coordinator.role_type == "student", Coordinator.status == "active")
            .count()
        )
        faculty_count = (
            db.session.query(Coordinator)
            .filter(
                Coordinator.role_type.in_(["faculty", "lead", "co-lead", "mentor"]),
                Coordinator.status == "active",
            )
            .count()
        )

        # Fetch ACTIVE coordinators + their Club + (optional) College
        rows = (
            db.session.query(Coordinator, Club, College)
            .join(Club, Coordinator.club_id == Club.club_id)
            .outerjoin(College, Coordinator.college_id == College.college_id)
            .filter(Coordinator.status == "active")
            .order_by(Coordinator.created_time.desc())
            .all()
        )

        # Shape data for the template (fields used by your coordinators.html)
        coordinators = []
        for coord, club, college in rows:
            coordinators.append({
                "id": coord.coordinator_id,
                "name": coord.coordinator_name,
                "club": club.club_name if club else "—",
                "club_id": coord.club_id,  # needed for edit modal
                "college_id": coord.college_id,  # needed for edit modal
                "type": coord.role_type or "—",
                "college_or_dept": coord.faculty_dept,
                "faculty_dept": coord.faculty_dept,
                "email": coord.email,
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

    # create coordinators
    @app.route("/coordinators/create", methods=["POST"])
    def assign_coordinator():
        name = (request.form.get("coordinator_name") or "").strip()
        club_id = request.form.get("club_id")
        college_id = request.form.get("college_id") or None
        faculty_dept = (request.form.get("faculty_dept") or "").strip()
        role_type = (request.form.get("role_type") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        description = (request.form.get("description") or "").strip()

        def back_to_modal():
            return redirect(url_for("coordinators") + "#coordinatorModal")

        # Validation
        if not name:
            flash("Coordinator name is required.", "error")
            return back_to_modal()
        if not club_id:
            flash("Club selection is required.", "error")
            return back_to_modal()

        # Optional image upload
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

            image_rel_path = os.path.relpath(save_path, current_app.static_folder)  # store as relative

        # Insert into DB
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
                status="active"
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

    # ---------- Announcements ----------
    @app.route("/announcements")
    def announcements():
        clubs = Club.query.order_by(Club.club_name.asc()).all()
        # Pinned first, then non-NULL publish_at (newest), NULLs last
        announcements = (
            Announcement.query
            .order_by(
                Announcement.pinned.desc(),
                Announcement.publish_at.is_(None),
                Announcement.publish_at.desc()
            )
            .all()
        )
        return render_template("announcements.html", clubs=clubs, announcements=announcements)

    #create announcement
    @app.route("/announcements/create", methods=["POST"])
    def create_announcement():
        # --- Fields ---
        title = (request.form.get("title") or "").strip()
        content = (request.form.get("content") or "").strip()
        club_id_raw = request.form.get("club_id")
        club_id = int(club_id_raw) if club_id_raw else None

        publish_date = request.form.get("publish_date")
        publish_time = request.form.get("publish_time")
        expire_date = request.form.get("expire_date")
        expire_time = request.form.get("expire_time")

        priority = (request.form.get("priority") or "normal").strip()
        audience = (request.form.get("audience") or "all_members").strip()
        status = (request.form.get("status") or "draft").strip()  # draft | published
        send_email = request.form.get("send_email") is not None
        pinned = request.form.get("pinned") is not None

        # --- Same helper style as Clubs ---
        def back_to_modal():
            return redirect(url_for("announcements"))

        # --- Basic validation (pre-parse) ---
        errors = []
        if not title:
            errors.append("Title is required.")
        if not content:
            errors.append("Content is required.")
        if status == "published" and not publish_date:
            errors.append("Publish date & time is required to publish.")

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

        # --- Save ---
        try:
            ann = Announcement(
                club_id=club_id,
                title=title,
                content=content,
                publish_at=publish_at,
                expire_at=expire_at,
                priority=priority,
                audience=audience,
                status=status,
                send_email=send_email,
                pinned=pinned,
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

    @app.route("/clubs/update", methods=["POST"])
    def update_club():
        f = request.form
        club_id = f.get("club_id", type=int)
        club = Club.query.get(club_id)
        if not club:
            flash("Club not found.", "error")
            return redirect(url_for("clubs"))

        club.club_name = (f.get("club_name") or "").strip() or club.club_name
        club.coordinator = (f.get("coordinator") or "").strip() or None
        club.club_category = (f.get("club_category") or "").strip() or None
        club.coordinator_type = (f.get("coordinator_type") or "").strip() or None
        club.description = (f.get("description") or "").strip() or None

        # Optional logo upload
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

        try:
            db.session.commit()
            flash("✅ Club updated successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to update club")
            flash("❌ Failed to update club.", "error")

        # Simple approach: reload page so the table reflects changes
        return redirect(url_for("clubs"))

    @app.route("/events/update", methods=["POST"])
    def update_event():
        f = request.form
        event_id = f.get("event_id", type=int)
        ev = Event.query.get(event_id)
        if not ev:
            flash("Event not found.", "error")
            return redirect(url_for("events"))

        # Validate club
        club_id = f.get("organising_club", type=int)
        if not club_id or not Club.query.get(club_id):
            flash("Please select a valid club.", "error")
            return redirect(url_for("events"))

        # Status guard
        EVENT_STATUS_VALUES = {"upcoming", "completed", "cancelled"}
        status = (f.get("status") or "upcoming").strip().lower()
        if status not in EVENT_STATUS_VALUES:
            flash("Invalid status selected.", "error")
            return redirect(url_for("events"))

        # Required name
        name = (f.get("event_name") or "").strip()
        if not name:
            flash("Event name is required.", "error")
            return redirect(url_for("events"))

        # Parse datetime (same helper as create)
        start_date = f.get("start_date")
        end_date = f.get("end_date")
        start_time = f.get("start_time")  # "HH:MM"
        end_time = f.get("end_time")  # "HH:MM"

        start_at = parse_dt(start_date, start_time)
        end_at = parse_dt(end_date, end_time)
        if not start_at or not end_at:
            flash("Please provide valid start and end date/time.", "error")
            return redirect(url_for("events"))
        if end_at <= start_at:
            flash("End time must be after start time.", "error")
            return redirect(url_for("events"))

        # Optional fields
        ev.event_name = name
        ev.organising_club_id = club_id
        ev.event_coordinator = (f.get("event_coordinator") or "").strip() or None
        ev.venue = (f.get("venue") or "").strip() or None
        ev.start_at = start_at
        ev.end_at = end_at
        ev.description = f.get("description") or ""
        ev.status = status

        max_participants = f.get("max_participants")
        ev.max_participants = int(max_participants) if max_participants and max_participants.isdigit() else None

        # Optional image upload
        file = request.files.get("event_image")
        if file and file.filename:
            allowed_ext = {"png", "jpg", "jpeg", "gif", "webp"}
            ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
            if ext not in allowed_ext:
                flash("Invalid image format. Allowed: png, jpg, jpeg, gif, webp.", "error")
                return redirect(url_for("events"))

            safe_name = secure_filename(file.filename)
            save_dir = current_app.config["EVENT_UPLOAD_FOLDER"]
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, safe_name)
            file.save(save_path)
            ev.event_image = relpath_from_static(save_path)  # store relative to /static

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
        if not col:
            flash("College not found.", "error")
            return redirect(url_for("colleges"))

        # Required name
        name = (f.get("college_name") or "").strip()
        if not name:
            flash("College name is required.", "error")
            return redirect(url_for("colleges"))

        # Ensure unique name (excluding itself)
        exists = College.query.filter(
            func.lower(College.college_name) == name.lower(),
            College.college_id != college_id
        ).first()
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
        if not co:
            flash("Coordinator not found.", "error")
            return redirect(url_for("coordinators"))

        # Required: name and club
        name = (f.get("coordinator_name") or "").strip()
        club_id = f.get("club_id", type=int)
        if not name:
            flash("Coordinator name is required.", "error")
            return redirect(url_for("coordinators"))
        if not club_id or not Club.query.get(club_id):
            flash("Please select a valid club.", "error")
            return redirect(url_for("coordinators"))

        # Optional: college
        college_id_raw = f.get("college_id")
        college_id = int(college_id_raw) if college_id_raw else None

        # Assign fields
        co.coordinator_name = name
        co.club_id = club_id
        co.college_id = college_id
        co.faculty_dept = (f.get("faculty_dept") or "").strip() or None
        co.role_type = (f.get("role_type") or "").strip() or None
        co.email = (f.get("email") or "").strip() or None
        co.phone = (f.get("phone") or "").strip() or None
        co.description = (f.get("description") or "").strip() or None

        # Optional: status select in edit (default/guard)
        status = (f.get("status") or co.status or "active").strip().lower()
        if status not in ("active", "inactive"):
            status = "active"
        co.status = status

        # Optional image upload (same pattern as your create route)
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
    @app.route("/announcements/update", methods=["POST"])
    def update_announcement():
        f = request.form
        ann_id = f.get("id", type=int)
        ann = Announcement.query.get(ann_id)
        if not ann:
            flash("Announcement not found.", "error")
            return redirect(url_for("announcements"))

        # Required
        title = (f.get("title") or "").strip()
        content = (f.get("content") or "").strip()
        if not title or not content:
            flash("Title and content are required.", "error")
            return redirect(url_for("announcements"))

        # Optional club
        club_id_raw = f.get("club_id")
        club_id = int(club_id_raw) if club_id_raw else None

        # Parse datetimes (reuse your helper)
        publish_date = f.get("publish_date")
        publish_time = f.get("publish_time")
        expire_date = f.get("expire_date")
        expire_time = f.get("expire_time")

        publish_at = parse_dt(publish_date, publish_time) if publish_date else None
        expire_at = parse_dt(expire_date, expire_time) if expire_date else None

        # Cross-field validation
        status = (f.get("status") or "draft").strip().lower()
        if status == "published" and not publish_at:
            flash("Publish date & time is required to publish.", "error")
            return redirect(url_for("announcements"))
        if publish_at and expire_at and expire_at <= publish_at:
            flash("Expiration must be after publish time.", "error")
            return redirect(url_for("announcements"))

        # Normalizations
        priority = (f.get("priority") or "normal").strip().lower()
        if priority not in ("normal", "high", "urgent"):
            priority = "normal"
        audience = (f.get("audience") or "all_members").strip().lower()
        pinned = f.get("pinned") is not None
        send_email = f.get("send_email") is not None

        # Apply
        ann.title = title
        ann.content = content
        ann.club_id = club_id
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

    @app.route("/profile")
    def profile():
       return render_template('profile.html')

    # DELETE OPERATIONS
    @app.route("/clubs/delete", methods=["POST"])
    def delete_club_form():
        """Delete a club from the admin UI (form submit version)."""
        club_id = request.form.get("club_id", type=int)
        club = Club.query.get(club_id)

        if not club:
            flash("❌ Club not found.", "error")
            return redirect(url_for("clubs"))

        try:
            db.session.delete(club)
            db.session.commit()
            flash("✅ Club deleted successfully!", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to delete club")
            flash("❌ Failed to delete club.", "error")

        return redirect(url_for("clubs"))
