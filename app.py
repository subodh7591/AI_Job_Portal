
from flask import Flask, redirect, url_for

from settings import Settings

from db_connector import db, login_manager

from database_models import (
    User,
    JobSeekerProfile,
    EmployerProfile,
    Job,
    JobApplication
)

from urls.authentication import authentication
from urls.job_seeker import job_seeker
from urls.employer import employer


# ============================================================
# APPLICATION INITIALISATION
# ============================================================

app = Flask(__name__)

app.config.from_object(Settings)


# ============================================================
# INITIALISE EXTENSIONS
# ============================================================

db.init_app(app)

login_manager.init_app(app)


# ============================================================
# USER SESSION MANAGEMENT
# ============================================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

app.register_blueprint(
    authentication
)

app.register_blueprint(
    job_seeker
)

app.register_blueprint(
    employer
)


# ============================================================
# HOME ROUTE
# ============================================================

@app.route("/")
def home():

    return redirect(
        url_for("authentication.login")
    )


# ============================================================
# DATABASE INITIALISATION
# ============================================================

with app.app_context():

    db.create_all()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
