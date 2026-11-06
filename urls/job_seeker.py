
import os
import uuid
import zipfile

from datetime import date, datetime, timezone

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    send_from_directory
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from db_connector import db

from database_models import (
    JobSeekerProfile,
    Job,
    EmployerProfile,
    JobApplication
)

from services.resume_parser import (
    extract_resume_text,
    parse_resume_with_gemini
)

from services.job_matcher import (
    match_jobs,
    calculate_skill_gap
)

from services.learning_resources import (
    get_learning_resources
)


job_seeker = Blueprint(
    "job_seeker",
    __name__,
    url_prefix="/job-seeker"
)


# ============================================================
# RESUME CONFIGURATION
# ============================================================

ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".docx"
}


# ============================================================
# JOB SEEKER ROLE CHECK
# ============================================================

def job_seeker_required():

    if current_user.role != "job_seeker":

        flash(
            "You do not have permission to access this page.",
            "danger"
        )

        return False

    return True


# ============================================================
# GET OR CREATE JOB SEEKER PROFILE
# ============================================================

def get_job_seeker_profile():

    profile = JobSeekerProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if profile is None:

        profile = JobSeekerProfile(
            user_id=current_user.id
        )

        db.session.add(profile)
        db.session.commit()

    return profile


# ============================================================
# RESUME FILE VALIDATION
# ============================================================

def is_valid_resume(uploaded_file):

    if not uploaded_file or not uploaded_file.filename:
        return False

    original_filename = secure_filename(
        uploaded_file.filename
    )

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_RESUME_EXTENSIONS:
        return False

    uploaded_file.stream.seek(0)

    file_signature = uploaded_file.stream.read(4)

    uploaded_file.stream.seek(0)

    # Check PDF signature.
    if extension == ".pdf":

        return file_signature.startswith(b"%PDF")

    # Check DOCX ZIP structure.
    if extension == ".docx":

        try:

            return zipfile.is_zipfile(
                uploaded_file.stream
            )

        except Exception:

            return False

        finally:

            uploaded_file.stream.seek(0)

    return False


# ============================================================
# JOB SEEKER PROFILE
# ============================================================

@job_seeker.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    job_seeker_profile = get_job_seeker_profile()

    if request.method == "POST":

        phone = request.form.get("phone", "").strip()
        location = request.form.get("location", "").strip()
        education = request.form.get("education", "").strip()
        experience = request.form.get("experience", "").strip()
        skills = request.form.get("skills", "").strip()
        bio = request.form.get("bio", "").strip()

        job_seeker_profile.phone = phone
        job_seeker_profile.location = location
        job_seeker_profile.education = education
        job_seeker_profile.experience = experience
        job_seeker_profile.skills = skills
        job_seeker_profile.bio = bio

        try:

            db.session.commit()

            flash(
                "Your profile has been updated successfully.",
                "success"
            )

        except Exception:

            db.session.rollback()

            flash(
                "An error occurred while updating your profile.",
                "danger"
            )

    return render_template(
        "job_seeker_profile.html",
        job_seeker_profile=job_seeker_profile
    )


# ============================================================
# UPLOAD OR REPLACE RESUME
# ============================================================

@job_seeker.route("/resume/upload", methods=["POST"])
@login_required
def upload_resume():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    uploaded_file = request.files.get("resume")

    if not uploaded_file or not uploaded_file.filename:

        flash(
            "Please select a resume to upload.",
            "danger"
        )

        return redirect(url_for("job_seeker.profile"))

    if not is_valid_resume(uploaded_file):

        flash(
            "Please upload a valid PDF or DOCX resume.",
            "danger"
        )

        return redirect(url_for("job_seeker.profile"))

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    os.makedirs(upload_folder, exist_ok=True)

    original_filename = secure_filename(
        uploaded_file.filename
    )

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    new_filename = uuid.uuid4().hex + extension

    new_file_path = os.path.join(
        upload_folder,
        new_filename
    )

    profile = get_job_seeker_profile()

    old_filename = profile.resume_filename

    # Save the new resume.
    try:

        uploaded_file.stream.seek(0)
        uploaded_file.save(new_file_path)

    except Exception:

        current_app.logger.exception(
            "Resume file upload failed."
        )

        flash(
            "The resume could not be uploaded.",
            "danger"
        )

        return redirect(url_for("job_seeker.profile"))

    # Update the database.
    try:

        profile.resume_filename = new_filename
        profile.parsed_resume_json = None
        profile.resume_parsed_at = None
        profile.resume_parse_status = "pending"

        db.session.commit()

    except Exception:

        db.session.rollback()

        if os.path.exists(new_file_path):
            os.remove(new_file_path)

        current_app.logger.exception(
            "Could not update resume information in the database."
        )

        flash(
            "The resume could not be saved to your profile.",
            "danger"
        )

        return redirect(url_for("job_seeker.profile"))

    # Remove the previous resume.
    if old_filename and old_filename != new_filename:

        old_file_path = os.path.join(
            upload_folder,
            old_filename
        )

        if os.path.isfile(old_file_path):

            try:
                os.remove(old_file_path)

            except OSError:

                current_app.logger.exception(
                    "Could not remove the previous resume file."
                )

    # Extract resume text and parse using Gemini.
    try:

        resume_text = extract_resume_text(new_file_path)

        if not resume_text.strip():

            raise ValueError(
                "No readable text was found in the resume."
            )

        parsed_data = parse_resume_with_gemini(
            resume_text=resume_text,
            api_key=current_app.config.get("GEMINI_API_KEY"),
            model_name=current_app.config.get(
                "GEMINI_MODEL",
                "gemini-2.5-flash"
            )
        )

        # Store the parsed JSON in the database.
        profile.parsed_resume_json = parsed_data

        profile.resume_parsed_at = datetime.now(
            timezone.utc
        )

        profile.resume_parse_status = "completed"

        db.session.commit()

        flash(
            "Your resume was uploaded and parsed successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        profile = get_job_seeker_profile()

        profile.parsed_resume_json = None
        profile.resume_parsed_at = None
        profile.resume_parse_status = "failed"

        db.session.commit()

        current_app.logger.exception(
            "Resume parsing failed."
        )

        flash(
            "Your resume was uploaded, but automatic parsing failed. "
            "Please check the file or try uploading it again.",
            "warning"
        )

    return redirect(url_for("job_seeker.profile"))


# ============================================================
# DOWNLOAD CURRENT RESUME
# ============================================================

@job_seeker.route("/resume/download", methods=["GET"])
@login_required
def download_resume():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    profile = get_job_seeker_profile()

    if not profile.resume_filename:

        flash(
            "You have not uploaded a resume.",
            "warning"
        )

        return redirect(url_for("job_seeker.profile"))

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        profile.resume_filename,
        as_attachment=True
    )


# ============================================================
# USE STORED RESUME JSON TO POPULATE PROFILE
# ============================================================

@job_seeker.route("/resume/use-for-profile", methods=["POST"])
@login_required
def use_resume_for_profile():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    profile = get_job_seeker_profile()

    parsed_data = profile.parsed_resume_json

    if not parsed_data:

        flash(
            "No successfully parsed resume information is available.",
            "warning"
        )

        return redirect(url_for("job_seeker.profile"))

    personal_info = parsed_data.get(
        "personal_information",
        {}
    )

    education_list = parsed_data.get("education", [])
    experience_list = parsed_data.get("experience", [])
    skills_list = parsed_data.get("skills", [])

    # Personal information.
    phone = personal_info.get("phone", "")
    location = personal_info.get("location", "")

    if phone:
        profile.phone = phone

    if location:
        profile.location = location

    # Education.
    if education_list:

        education_entries = []

        for item in education_list:

            entry = (
                "Qualification: "
                + item.get("qualification", "")
                + "\nInstitution: "
                + item.get("institution", "")
                + "\nYear: "
                + item.get("year", "")
                + "\nDetails: "
                + item.get("details", "")
            )

            education_entries.append(entry)

        profile.education = "\n\n".join(
            education_entries
        )

    # Experience.
    if experience_list:

        experience_entries = []

        for item in experience_list:

            responsibilities = item.get(
                "responsibilities",
                []
            )

            entry = (
                "Job title: "
                + item.get("job_title", "")
                + "\nCompany: "
                + item.get("company", "")
                + "\nDuration: "
                + item.get("duration", "")
                + "\nResponsibilities: "
                + ", ".join(responsibilities)
            )

            experience_entries.append(entry)

        profile.experience = "\n\n".join(
            experience_entries
        )

    # Skills.
    if skills_list:

        profile.skills = ", ".join(
            skills_list
        )

    # Professional summary.
    summary = parsed_data.get(
        "professional_summary",
        ""
    )

    if summary:
        profile.bio = summary

    # Save profile.
    try:

        db.session.commit()

        flash(
            "Your profile has been populated using your resume. "
            "Please review the information.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "An error occurred while updating your profile.",
            "danger"
        )

    return redirect(url_for("job_seeker.profile"))


# ============================================================
# BROWSE JOBS
# ============================================================

@job_seeker.route("/jobs")
@login_required
def jobs():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    search = request.args.get("search", "").strip()
    location = request.args.get("location", "").strip()
    employment_type = request.args.get(
        "employment_type", ""
    ).strip()
    workplace_type = request.args.get(
        "workplace_type", ""
    ).strip()
    experience_level = request.args.get(
        "experience_level", ""
    ).strip()

    jobs_query = Job.query.filter(
        Job.status == "open",
        db.or_(
            Job.closing_date.is_(None),
            Job.closing_date >= date.today()
        )
    )

    if search:

        search_term = f"%{search}%"

        jobs_query = jobs_query.filter(
            db.or_(
                Job.title.ilike(search_term),
                Job.description.ilike(search_term),
                Job.required_skills.ilike(search_term),
                Job.preferred_skills.ilike(search_term),
                Job.qualifications.ilike(search_term)
            )
        )

    if location:

        jobs_query = jobs_query.filter(
            Job.location.ilike(f"%{location}%")
        )

    if employment_type:

        jobs_query = jobs_query.filter(
            Job.employment_type == employment_type
        )

    if workplace_type:

        jobs_query = jobs_query.filter(
            Job.workplace_type == workplace_type
        )

    if experience_level:

        jobs_query = jobs_query.filter(
            Job.experience_level == experience_level
        )

    available_jobs = jobs_query.order_by(
        Job.created_at.desc()
    ).all()

    return render_template(
        "job_seeker_jobs.html",
        jobs=available_jobs,
        search=search,
        location=location,
        employment_type=employment_type,
        workplace_type=workplace_type,
        experience_level=experience_level
    )


# ============================================================
# JOB DETAILS
# ============================================================

@job_seeker.route("/jobs/<int:job_id>")
@login_required
def job_details(job_id):

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    job = Job.query.filter(
        Job.id == job_id,
        Job.status == "open",
        db.or_(
            Job.closing_date.is_(None),
            Job.closing_date >= date.today()
        )
    ).first_or_404()

    employer_profile = EmployerProfile.query.get_or_404(
        job.employer_id
    )

    existing_application = JobApplication.query.filter_by(
        job_id=job.id,
        job_seeker_id=current_user.id
    ).first()

    job_seeker_profile = get_job_seeker_profile()

    return render_template(
        "job_seeker_job_details.html",
        job=job,
        employer_profile=employer_profile,
        existing_application=existing_application,
        job_seeker_profile=job_seeker_profile
    )


# ============================================================
# APPLY FOR A JOB
# ============================================================

@job_seeker.route("/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_for_job(job_id):

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    job = Job.query.filter(
        Job.id == job_id,
        Job.status == "open",
        db.or_(
            Job.closing_date.is_(None),
            Job.closing_date >= date.today()
        )
    ).first()

    if job is None:

        flash(
            "This vacancy is no longer available.",
            "danger"
        )

        return redirect(url_for("job_seeker.jobs"))

    existing_application = JobApplication.query.filter_by(
        job_id=job.id,
        job_seeker_id=current_user.id
    ).first()

    if existing_application:

        flash(
            "You have already applied for this vacancy.",
            "warning"
        )

        return redirect(
            url_for("job_seeker.job_details", job_id=job.id)
        )

    cover_letter = request.form.get(
        "cover_letter",
        ""
    ).strip()

    application = JobApplication(
        job_id=job.id,
        job_seeker_id=current_user.id,
        cover_letter=cover_letter,
        status="submitted"
    )

    db.session.add(application)

    try:

        db.session.commit()

        flash(
            "Your application has been submitted successfully.",
            "success"
        )

        return redirect(
            url_for("job_seeker.my_applications")
        )

    except Exception:

        db.session.rollback()

        flash(
            "An error occurred while submitting your application. "
            "Please try again.",
            "danger"
        )

        return redirect(
            url_for("job_seeker.job_details", job_id=job.id)
        )


# ============================================================
# MY APPLICATIONS
# ============================================================

@job_seeker.route("/my-applications")
@login_required
def my_applications():

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    applications = JobApplication.query.filter_by(
        job_seeker_id=current_user.id
    ).order_by(
        JobApplication.applied_at.desc()
    ).all()

    return render_template(
        "job_seeker_applications.html",
        applications=applications
    )


# ============================================================
# RECOMMENDED JOBS
# ============================================================

@job_seeker.route("/recommended-jobs")
@login_required
def recommended_jobs():

    if not job_seeker_required():

        return redirect(
            url_for("authentication.login")
        )

    job_seeker_profile = get_job_seeker_profile()

    if not job_seeker_profile.resume_filename:

        flash(
            "Please upload your resume before viewing job recommendations.",
            "warning"
        )

        return redirect(
            url_for("job_seeker.profile")
        )

    if (
        job_seeker_profile.resume_parse_status != "completed"
        or not job_seeker_profile.parsed_resume_json
    ):

        flash(
            "Your resume has not been successfully processed. "
            "Please upload or process your resume again.",
            "warning"
        )

        return redirect(
            url_for("job_seeker.profile")
        )

    method = request.args.get(
        "method",
        "semantic"
    ).lower()

    if method not in {"keyword", "semantic"}:
        method = "semantic"

    available_jobs = Job.query.filter(
        Job.status == "open",
        db.or_(
            Job.closing_date.is_(None),
            Job.closing_date >= date.today()
        )
    ).all()

    if not available_jobs:

        flash(
            "There are currently no available jobs to recommend.",
            "info"
        )

        return render_template(
            "job_seeker_recommended_jobs.html",
            recommendations=[],
            method=method
        )

    try:

        recommendations = match_jobs(
            parsed_resume=job_seeker_profile.parsed_resume_json,
            jobs=available_jobs,
            method=method,
            top_n=20
        )

    except Exception:

        current_app.logger.exception(
            "Job matching failed."
        )

        flash(
            "Unable to generate job recommendations. "
            "Please try again later.",
            "danger"
        )

        return redirect(
            url_for("job_seeker.jobs")
        )

    return render_template(
        "job_seeker_recommended_jobs.html",
        recommendations=recommendations,
        method=method
    )


# ============================================================
# JOB SKILL GAP ANALYSIS AND LEARNING RECOMMENDATIONS
# ============================================================

@job_seeker.route("/jobs/<int:job_id>/skill-gap")
@login_required
def skill_gap(job_id):

    if not job_seeker_required():
        return redirect(url_for("authentication.login"))

    # Retrieve the job seeker's profile.
    job_seeker_profile = get_job_seeker_profile()

    # Check whether a resume has been uploaded and parsed.
    if (
        not job_seeker_profile.resume_filename
        or job_seeker_profile.resume_parse_status != "completed"
        or not job_seeker_profile.parsed_resume_json
    ):

        flash(
            "Please upload and successfully parse your resume "
            "before viewing the skill gap analysis.",
            "warning"
        )

        return redirect(
            url_for("job_seeker.profile")
        )

    # Retrieve the selected job.
    job = Job.query.filter(
        Job.id == job_id,
        Job.status == "open",
        db.or_(
            Job.closing_date.is_(None),
            Job.closing_date >= date.today()
        )
    ).first_or_404()

    try:

        # Generate the skill gap report.
        skill_gap_report = calculate_skill_gap(
            parsed_resume=job_seeker_profile.parsed_resume_json,
            job=job
        )

        # Combine missing required and preferred skills.
        missing_skills = (
            skill_gap_report.get("missing_required_skills", [])
            +
            skill_gap_report.get("missing_preferred_skills", [])
        )

        # Generate learning-resource recommendations.
        learning_recommendations = get_learning_resources(
            missing_skills=missing_skills,
            max_resources_per_skill=3
        )

    except Exception:

        current_app.logger.exception(
            "Skill gap analysis or learning recommendations failed "
            "for job %s.",
            job_id
        )

        flash(
            "Unable to generate the skill gap analysis. "
            "Please try again later.",
            "danger"
        )

        return redirect(
            url_for("job_seeker.job_details", job_id=job.id)
        )

    return render_template(
        "job_seeker_skill_gap.html",
        job=job,
        skill_gap_report=skill_gap_report,
        learning_recommendations=learning_recommendations
    )
