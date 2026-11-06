
from datetime import datetime

from sqlalchemy import UniqueConstraint

from flask_login import UserMixin

from db_connector import db


# ============================================================
# USER
# ============================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        default="job_seeker"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Job seeker profile
    job_seeker_profile = db.relationship(
        "JobSeekerProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Employer profile
    employer_profile = db.relationship(
        "EmployerProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Applications submitted by this user
    applications = db.relationship(
        "JobApplication",
        foreign_keys="JobApplication.job_seeker_id",
        backref="job_seeker",
        cascade="all, delete-orphan"
    )


# ============================================================
# JOB SEEKER PROFILE
# ============================================================

class JobSeekerProfile(db.Model):

    __tablename__ = "job_seeker_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    # Existing profile information
    phone = db.Column(db.String(30))

    location = db.Column(db.String(150))

    education = db.Column(db.Text)

    experience = db.Column(db.Text)

    skills = db.Column(db.Text)

    bio = db.Column(db.Text)

    # Resume information
    resume_filename = db.Column(
        db.String(255),
        nullable=True
    )

    parsed_resume_json = db.Column(
        db.JSON,
        nullable=True
    )

    resume_parsed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    resume_parse_status = db.Column(
        db.String(20),
        nullable=True,
        default=None
    )


# ============================================================
# EMPLOYER PROFILE
# ============================================================

class EmployerProfile(db.Model):

    __tablename__ = "employer_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    industry = db.Column(
        db.String(100)
    )

    website = db.Column(
        db.String(255)
    )

    company_size = db.Column(
        db.String(50)
    )

    location = db.Column(
        db.String(150)
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Jobs posted by this employer
    jobs = db.relationship(
        "Job",
        backref="employer",
        cascade="all, delete-orphan"
    )


# ============================================================
# JOB
# ============================================================

class Job(db.Model):

    __tablename__ = "jobs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employer_id = db.Column(
        db.Integer,
        db.ForeignKey("employer_profiles.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    location = db.Column(
        db.String(150)
    )

    employment_type = db.Column(
        db.String(50)
    )

    workplace_type = db.Column(
        db.String(50)
    )

    experience_level = db.Column(
        db.String(100)
    )

    salary_min = db.Column(
        db.Float
    )

    salary_max = db.Column(
        db.Float
    )

    salary_currency = db.Column(
        db.String(10),
        default="GBP"
    )

    required_skills = db.Column(
        db.Text
    )

    preferred_skills = db.Column(
        db.Text
    )

    qualifications = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="open"
    )

    closing_date = db.Column(
        db.Date
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ========================================================
    # SEMANTIC JOB EMBEDDING
    # ========================================================

    # Stores the numerical vector generated from job information.
    # JSON allows the vector to be stored directly in SQLite.
    job_embedding = db.Column(
        db.JSON,
        nullable=True
    )

    # Records the Sentence Transformer model used.
    embedding_model = db.Column(
        db.String(150),
        nullable=True
    )

    # Records when the embedding was last generated.
    embedding_generated_at = db.Column(
        db.DateTime,
        nullable=True
    )

    # Applications received for this job
    applications = db.relationship(
        "JobApplication",
        backref="job",
        cascade="all, delete-orphan"
    )


# ============================================================
# JOB APPLICATION
# ============================================================

class JobApplication(db.Model):

    __tablename__ = "job_applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    job_seeker_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    cover_letter = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="submitted"
    )

    applied_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Prevent duplicate applications
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "job_seeker_id",
            name="unique_job_seeker_application"
        ),
    )
