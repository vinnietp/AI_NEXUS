from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

#########33

class College(db.Model):
    __tablename__ = "colleges"

    college_id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(120), nullable=False, unique=True)

    # NEW FIELDS
    authority_name = db.Column(db.String(120))   # e.g., Dr. John Doe
    authority_role = db.Column(db.String(30))    # principal|hod|faculty|admin|other
    phone          = db.Column(db.String(20))
    description    = db.Column(db.Text)

    # Existing fields (keep as you had)
    email    = db.Column(db.String(120))
    location = db.Column(db.String(120))
    status   = db.Column(db.String(20), default="active")  # active|inactive
    created_time = db.Column(db.DateTime, default=datetime.now)  # naive IST by convention
    status = db.Column(db.String(20), default="active", nullable=False)

    coordinators = db.relationship(
        "Coordinator",
        back_populates="college",
        lazy=True,
    )

    # Optional relationship if you load clubs via College.clubs
    # clubs = db.relationship("Club", backref="college", lazy="select")

# Keep your club as-is
class Club(db.Model):
    __tablename__ = "clubs"

    club_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    club_name = db.Column(db.String(100), nullable=False)
    club_category = db.Column(db.String(50))
    coordinator = db.Column(db.String(100))
    coordinator_type = db.Column(db.String(50))
    club_logo = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.now,nullable=False)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,nullable=False)

    # ✅ New column
    status = db.Column(db.String(20), default="active", nullable=False)

    # Relationships
    events = db.relationship("Event", back_populates="club", cascade="all,delete-orphan")
    coordinators = db.relationship(
        "Coordinator",
        back_populates="club",
        cascade="all,delete-orphan"
    )

    def __repr__(self):
        return f"<Club {self.club_id} {self.club_name!r} status={self.status!r}>"

    ######################
# Event with FK + simple status
EVENT_STATUS_VALUES = ("upcoming", "completed", "cancelled")

class Event(db.Model):
    __tablename__ = "events"

    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Basic details
    event_name = db.Column(db.String(150), nullable=False)
    organising_club_id = db.Column(
        db.Integer,
        db.ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_coordinator = db.Column(db.String(100))
    venue = db.Column(db.String(150))

    # Schedule (store UTC; convert to/from local in routes)
    start_at = db.Column(db.DateTime, nullable=False)  # UTC
    end_at   = db.Column(db.DateTime, nullable=False)  # UTC

    # Media & meta
    event_image = db.Column(db.String(255))
    max_participants = db.Column(db.Integer)
    status = db.Column(db.String(20), default="upcoming", nullable=False)  # one of EVENT_STATUS_VALUES
    description = db.Column(db.Text)

    # Audit
    created_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationship
    club = db.relationship("Club", back_populates="events")

    def __repr__(self):
        return f"<Event {self.event_id} {self.event_name!r} {self.start_at}->{self.end_at}>"



# --------------------------
# Coordinator
# --------------------------
    # models.py
class Coordinator(db.Model):
    __tablename__ = "coordinators"

    coordinator_id   = db.Column(db.Integer, primary_key=True)
    coordinator_name = db.Column(db.String(100), nullable=False)

    club_id = db.Column(
        db.Integer,
        db.ForeignKey("clubs.club_id", ondelete="CASCADE"),
        nullable=False
    )
    college_id = db.Column(
        db.Integer,
        db.ForeignKey("colleges.college_id", ondelete="SET NULL"),
        nullable=True
    )

    faculty_dept = db.Column(db.String(100))
    role_type    = db.Column(db.String(50))
    email        = db.Column(db.String(120))
    phone        = db.Column(db.String(20))
    coordinator_image = db.Column(db.String(255))
    description       = db.Column(db.Text)
    created_time = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    status = db.Column(db.String(20), default="active", nullable=False)


    # <-- IMPORTANT: use back_populates to pair with the parent sides above
    club    = db.relationship("Club", back_populates="coordinators")
    college = db.relationship("College", back_populates="coordinators")

    # def __repr__(self):
    #     return f"<Coordinator {self.coordinator_id} {self.coordinator_name!r} ch={self.club_id}>"



# models.py

class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.club_id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    publish_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expire_at  = db.Column(db.DateTime(timezone=True), nullable=True)

    priority = db.Column(db.String(20), default="normal")  # normal | high | urgent
    audience = db.Column(db.String(50), default="all_members")

    status = db.Column(db.String(20), default="draft")     # draft | published

    send_email = db.Column(db.Boolean, default=False)
    pinned     = db.Column(db.Boolean, default=False)

    created_at= db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    # updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships (optional)
    club = db.relationship("Club", backref="announcements", lazy=True)
