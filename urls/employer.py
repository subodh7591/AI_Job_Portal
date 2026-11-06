
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from db_connector import db

from database_models import (
    EmployerProfile,
    Job,
    JobApplication
)

from services.job_matcher import prepare_job_embedding


employer = Blueprint(
    "employer",
    __name__,
    url_prefix="/employer"
)


# ============================================================
# EMPLOYER ACCESS CONTROL
# ============================================================

def employer_required():

    if current_user.role != "employer":

        flash(
            "You are not authorised to access this page.",
            "error"
        )

        return False

    return True


def get_employer_profile():

    return EmployerProfile.query.filter_by(
        user_id=current_user.id
    ).first()


# ============================================================
# GENERATE JOB EMBEDDING
# ============================================================

def update_job_embedding(job):

    """
    Generate and assign a new semantic embedding.

    If generation fails, clear any previous embedding.
    This prevents recommendations from using outdated vectors.

    Returns:
        True if successful, otherwise False.
    """

    try:

        prepare_job_embedding(job)

        return True

    except Exception as error:

        print(
            f"Job embedding generation failed for job "
            f"{job.id}: {error}"
        )

        job.job_embedding = None
        job.embedding_model = None
        job.embedding_generated_at = None

        return False


# ============================================================
# GET JOB FORM DATA
# ============================================================

def get_job_form_data():

    title = request.form.get("title", "").strip()

    description = request.form.get("description", "").strip()

    location = request.form.get("location", "").strip()

    employment_type = request.form.get(
        "employment_type", ""
    ).strip()

    workplace_type = request.form.get(
        "workplace_type", ""
    ).strip()

    experience_level = request.form.get(
        "experience_level", ""
    ).strip()

    salary_min_value = request.form.get(
        "salary_min", ""
    ).strip()

    salary_max_value = request.form.get(
        "salary_max", ""
    ).strip()

    salary_currency = request.form.get(
        "salary_currency", "GBP"
    ).strip()

    required_skills = request.form.get(
        "required_skills", ""
    ).strip()

    preferred_skills = request.form.get(
        "preferred_skills", ""
    ).strip()

    qualifications = request.form.get(
        "qualifications", ""
    ).strip()

    closing_date_value = request.form.get(
        "closing_date", ""
    ).strip()

    if not title or not description:

        return None, "Job title and description are required."

    # Validate salary values.
    try:

        salary_min = (
            float(salary_min_value)
            if salary_min_value else None
        )

        salary_max = (
            float(salary_max_value)
            if salary_max_value else None
        )

        if salary_min is not None and salary_min < 0:
            raise ValueError

        if salary_max is not None and salary_max < 0:
            raise ValueError

    except ValueError:

        return None, "Please enter valid, non-negative salary amounts."

    if (
        salary_min is not None
        and salary_max is not None
        and salary_min > salary_max
    ):

        return None, "Minimum salary cannot be greater than maximum salary."

    # Validate closing date.
    closing_date = None

    if closing_date_value:

        try:

            closing_date = datetime.strptime(
                closing_date_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return None, "Please enter a valid closing date."

    job_data = {

        "title": title,

        "description": description,

        "location": location,

        "employment_type": employment_type,

        "workplace_type": workplace_type,

        "experience_level": experience_level,

        "salary_min": salary_min,

        "salary_max": salary_max,

        "salary_currency": salary_currency,

        "required_skills": required_skills,

        "preferred_skills": preferred_skills,

        "qualifications": qualifications,

        "closing_date": closing_date

    }

    return job_data, None


# ============================================================
# EMPLOYER DASHBOARD
# ============================================================

@employer.route("/dashboard")
@login_required
def dashboard():

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        flash(
            "Please complete your company profile.",
            "info"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    total_jobs = Job.query.filter_by(
        employer_id=employer_profile.id
    ).count()

    open_jobs = Job.query.filter_by(
        employer_id=employer_profile.id,
        status="open"
    ).count()

    closed_jobs = Job.query.filter_by(
        employer_id=employer_profile.id,
        status="closed"
    ).count()

    total_applications = (
        JobApplication.query
        .join(Job)
        .filter(Job.employer_id == employer_profile.id)
        .count()
    )

    recent_jobs = (
        Job.query
        .filter_by(employer_id=employer_profile.id)
        .order_by(Job.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "employer/dashboard.html",
        employer_profile=employer_profile,
        total_jobs=total_jobs,
        open_jobs=open_jobs,
        closed_jobs=closed_jobs,
        total_applications=total_applications,
        recent_jobs=recent_jobs
    )


# ============================================================
# COMPANY PROFILE
# ============================================================

@employer.route(
    "/company-profile",
    methods=["GET", "POST"]
)
@login_required
def company_profile():

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if request.method == "POST":

        company_name = request.form.get(
            "company_name", ""
        ).strip()

        industry = request.form.get(
            "industry", ""
        ).strip()

        website = request.form.get(
            "website", ""
        ).strip()

        company_size = request.form.get(
            "company_size", ""
        ).strip()

        location = request.form.get(
            "location", ""
        ).strip()

        description = request.form.get(
            "description", ""
        ).strip()

        if not company_name:

            flash("Company name is required.", "error")

            return render_template(
                "employer/company_profile.html",
                employer_profile=employer_profile
            )

        if not employer_profile:

            employer_profile = EmployerProfile(
                user_id=current_user.id,
                company_name=company_name
            )

            db.session.add(employer_profile)

        employer_profile.company_name = company_name
        employer_profile.industry = industry
        employer_profile.website = website
        employer_profile.company_size = company_size
        employer_profile.location = location
        employer_profile.description = description

        try:

            db.session.commit()

            flash(
                "Company profile saved successfully.",
                "success"
            )

            return redirect(
                url_for("employer.company_profile")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Unable to save company profile. Please try again.",
                "error"
            )

    return render_template(
        "employer/company_profile.html",
        employer_profile=employer_profile
    )


# ============================================================
# POST A JOB
# ============================================================

@employer.route(
    "/post-job",
    methods=["GET", "POST"]
)
@login_required
def post_job():

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        flash(
            "Please complete your company profile before posting a job.",
            "info"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    if request.method == "POST":

        job_data, error = get_job_form_data()

        if error:

            flash(error, "error")

            return render_template(
                "employer/post_job.html"
            )

        new_job = Job(
            employer_id=employer_profile.id,
            status="open",
            **job_data
        )

        db.session.add(new_job)

        try:

            # Generate the embedding before saving.
            embedding_generated = update_job_embedding(
                new_job
            )

            db.session.commit()

            if embedding_generated:

                flash(
                    "Your job vacancy has been published successfully "
                    "and its semantic embedding has been generated.",
                    "success"
                )

            else:

                flash(
                    "Your job vacancy was published, but its semantic "
                    "embedding could not be generated. It will need "
                    "embedding generation before semantic recommendations "
                    "can include it.",
                    "warning"
                )

            return redirect(
                url_for("employer.manage_jobs")
            )

        except Exception as error:

            db.session.rollback()

            print(f"Job publishing error: {error}")

            flash(
                "Unable to publish the job vacancy. Please try again.",
                "error"
            )

    return render_template(
        "employer/post_job.html"
    )


# ============================================================
# MANAGE JOBS
# ============================================================

@employer.route("/manage-jobs")
@login_required
def manage_jobs():

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        flash(
            "Please complete your company profile first.",
            "info"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    jobs = (
        Job.query
        .filter_by(employer_id=employer_profile.id)
        .order_by(Job.created_at.desc())
        .all()
    )

    return render_template(
        "employer/manage_jobs.html",
        jobs=jobs
    )


# ============================================================
# EDIT JOB
# ============================================================

@employer.route(
    "/edit-job/<int:job_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_job(job_id):

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        return redirect(
            url_for("employer.company_profile")
        )

    # Only allow employers to edit their own jobs.
    job = Job.query.filter_by(
        id=job_id,
        employer_id=employer_profile.id
    ).first_or_404()

    if request.method == "POST":

        job_data, error = get_job_form_data()

        if error:

            flash(error, "error")

            return render_template(
                "employer/edit_job.html",
                job=job
            )

        for field, value in job_data.items():

            setattr(job, field, value)

        try:

            # Regenerate the embedding using the updated job details.
            embedding_generated = update_job_embedding(job)

            db.session.commit()

            if embedding_generated:

                flash(
                    "Job vacancy updated successfully and its "
                    "semantic embedding has been regenerated.",
                    "success"
                )

            else:

                flash(
                    "Job vacancy updated successfully, but its semantic "
                    "embedding could not be regenerated. The old embedding "
                    "was cleared to prevent outdated recommendations.",
                    "warning"
                )

            return redirect(
                url_for("employer.manage_jobs")
            )

        except Exception as error:

            db.session.rollback()

            print(f"Job update error: {error}")

            flash(
                "Unable to update the job vacancy. Please try again.",
                "error"
            )

    return render_template(
        "employer/edit_job.html",
        job=job
    )


# ============================================================
# CLOSE OR REOPEN JOB
# ============================================================

@employer.route(
    "/change-job-status/<int:job_id>",
    methods=["POST"]
)
@login_required
def change_job_status(job_id):

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        return redirect(
            url_for("employer.company_profile")
        )

    job = Job.query.filter_by(
        id=job_id,
        employer_id=employer_profile.id
    ).first_or_404()

    new_status = request.form.get(
        "status", ""
    ).strip()

    if new_status not in ["open", "closed"]:

        flash(
            "Invalid job status.",
            "error"
        )

        return redirect(
            url_for("employer.manage_jobs")
        )

    job.status = new_status

    try:

        db.session.commit()

        if new_status == "closed":

            flash(
                "Job vacancy closed successfully.",
                "success"
            )

        else:

            flash(
                "Job vacancy reopened successfully.",
                "success"
            )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to update the job status.",
            "error"
        )

    return redirect(
        url_for("employer.manage_jobs")
    )


# ============================================================
# DELETE JOB
# ============================================================

@employer.route(
    "/delete-job/<int:job_id>",
    methods=["POST"]
)
@login_required
def delete_job(job_id):

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        return redirect(
            url_for("employer.company_profile")
        )

    job = Job.query.filter_by(
        id=job_id,
        employer_id=employer_profile.id
    ).first_or_404()

    application_count = JobApplication.query.filter_by(
        job_id=job.id
    ).count()

    if application_count > 0:

        flash(
            "This vacancy has applications and cannot be deleted. "
            "Close it instead.",
            "error"
        )

        return redirect(
            url_for("employer.manage_jobs")
        )

    try:

        db.session.delete(job)

        db.session.commit()

        flash(
            "Job vacancy deleted successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete the job vacancy.",
            "error"
        )

    return redirect(
        url_for("employer.manage_jobs")
    )


# ============================================================
# VIEW APPLICATIONS
# ============================================================

@employer.route("/jobs/<int:job_id>/applications")
@login_required
def job_applications(job_id):

    if not employer_required():

        return redirect(url_for("job_seeker.profile"))

    employer_profile = get_employer_profile()

    if not employer_profile:

        flash(
            "Please complete your company profile first.",
            "warning"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    job = Job.query.filter_by(
        id=job_id,
        employer_id=employer_profile.id
    ).first_or_404()

    applications = (
        JobApplication.query
        .filter_by(job_id=job.id)
        .order_by(JobApplication.applied_at.desc())
        .all()
    )

    return render_template(
        "employer/applications.html",
        job=job,
        applications=applications
    )


# ============================================================
# VIEW APPLICANT DETAILS
# ============================================================

@employer.route("/applications/<int:application_id>")
@login_required
def application_details(application_id):

    if not employer_required():

        return redirect(url_for("authentication.login"))

    employer_profile = get_employer_profile()

    if employer_profile is None:

        flash(
            "Please complete your company profile first.",
            "warning"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    application = (
        JobApplication.query
        .join(Job, JobApplication.job_id == Job.id)
        .filter(
            JobApplication.id == application_id,
            Job.employer_id == employer_profile.id
        )
        .first_or_404()
    )

    applicant = application.job_seeker

    applicant_profile = applicant.job_seeker_profile

    return render_template(
        "employer/application_details.html",
        application=application,
        applicant=applicant,
        applicant_profile=applicant_profile
    )


# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@employer.route(
    "/applications/<int:application_id>/status",
    methods=["POST"]
)
@login_required
def update_application_status(application_id):

    if not employer_required():

        return redirect(url_for("authentication.login"))

    employer_profile = get_employer_profile()

    if employer_profile is None:

        flash(
            "Please complete your company profile first.",
            "warning"
        )

        return redirect(
            url_for("employer.company_profile")
        )

    application = (
        JobApplication.query
        .join(Job, JobApplication.job_id == Job.id)
        .filter(
            JobApplication.id == application_id,
            Job.employer_id == employer_profile.id
        )
        .first_or_404()
    )

    allowed_statuses = [
        "submitted",
        "under_review",
        "shortlisted",
        "interview",
        "accepted",
        "rejected"
    ]

    new_status = request.form.get(
        "status", ""
    ).strip()

    if new_status not in allowed_statuses:

        flash(
            "Invalid application status.",
            "danger"
        )

        return redirect(
            url_for(
                "employer.application_details",
                application_id=application.id
            )
        )

    application.status = new_status

    try:

        db.session.commit()

        flash(
            "Application status updated successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "An error occurred while updating the application status.",
            "danger"
        )

    return redirect(
        url_for(
            "employer.application_details",
            application_id=application.id
        )
    )
