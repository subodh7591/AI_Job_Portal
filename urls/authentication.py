
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from db_connector import db

from database_models import (
    User,
    EmployerProfile
)


authentication = Blueprint(
    "authentication",
    __name__
)


# ============================================================
# REGISTRATION
# ============================================================

@authentication.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        if current_user.role == "employer":
            return redirect(
                url_for("employer.dashboard")
            )

        return redirect(
            url_for("job_seeker.profile")
        )

    if request.method == "POST":

        first_name = request.form.get(
            "first_name", ""
        ).strip()

        last_name = request.form.get(
            "last_name", ""
        ).strip()

        username = request.form.get(
            "username", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        role = request.form.get(
            "role", "job_seeker"
        ).strip()

        company_name = request.form.get(
            "company_name", ""
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not all([
            first_name,
            last_name,
            username,
            email,
            password
        ]):

            flash(
                "Please complete all required fields.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        if role not in ["job_seeker", "employer"]:

            flash(
                "Invalid account type selected.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        if role == "employer" and not company_name:

            flash(
                "Please enter your company name.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        # ----------------------------------------------------
        # CHECK EXISTING USERNAME
        # ----------------------------------------------------

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        # ----------------------------------------------------
        # CHECK EXISTING EMAIL
        # ----------------------------------------------------

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:

            flash(
                "Email already registered.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=hashed_password,
            role=role
        )

        try:

            db.session.add(new_user)

            # Create employer profile automatically
            if role == "employer":

                employer_profile = EmployerProfile(
                    user=new_user,
                    company_name=company_name
                )

                db.session.add(employer_profile)

            db.session.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("authentication.login")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Registration failed. Please try again.",
                "error"
            )

            return redirect(
                url_for("authentication.register")
            )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@authentication.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        if current_user.role == "employer":
            return redirect(
                url_for("employer.dashboard")
            )

        return redirect(
            url_for("job_seeker.profile")
        )

    if request.method == "POST":

        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            if user.role == "employer":

                return redirect(
                    url_for("employer.dashboard")
                )

            return redirect(
                url_for("job_seeker.profile")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@authentication.route("/logout")
def logout():

    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("authentication.login")
    )
