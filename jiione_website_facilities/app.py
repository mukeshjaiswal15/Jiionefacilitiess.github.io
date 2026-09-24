"""
Jii One Facilities — website backend
Flask + MongoDB (pymongo)

Two separate auth systems, kept in separate collections so a client
account can never accidentally get admin rights:
  - users  collection  -> client/customer login   (session['user_id'])
  - admins collection -> staff/admin login        (session['admin_id'])
"""

import os
from datetime import datetime, timezone

import certifi

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup


# ----------------------------------------------------------------------
# App & database setup
# ----------------------------------------------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-secret-change-this"
)

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

# MongoDB Atlas TLS/SSL connection
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=8000
)

db = client[
    os.environ.get(
        "MONGO_DBNAME",
        "jiione_facilities"
    )
]

users_col = db["users"]
admins_col = db["admins"]
enquiries_col = db["enquiries"]
requests_col = db["service_requests"]


# ----------------------------------------------------------------------
# Static site content
# ----------------------------------------------------------------------

ICONS = {
    "broom": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 4 10 14"/><path d="M10 14 6 22l4-2 2-4 4 2-2-4"/><circle cx="19.5" cy="4.5" r="1.4" fill="currentColor" stroke="none"/></svg>',

    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v6c0 5 3.4 8.4 8 9 4.6-.6 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/></svg>',

    "cup": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8Z"/><path d="M17 9h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M8 3c0 1-1 1-1 2s1 1 1 2M12 3c0 1-1 1-1 2s1 1 1 2"/></svg>',

    "building": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="10" height="18"/><path d="M14 8h6v13h-6M7 7h1M11 7h1M7 11h1M11 11h1M7 15h1M11 15h1"/></svg>',

    "bug": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="8" width="8" height="11" rx="4"/><path d="M12 8V5M9 5 7 3M15 5l2-2M4 11l4 1M20 11l-4 1M4 18l4-1M20 18l-4-1"/></svg>',

    "chart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>',

    "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M2 20c0-3.3 3-6 7-6s7 2.7 7 6"/><circle cx="17" cy="8" r="2.6"/><path d="M16 14.2c2.7.5 5 2.6 5 5.8"/></svg>',

    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="12" height="10"/><path d="M14 10h4l4 3.5V17h-8"/><circle cx="6.5" cy="19" r="1.8"/><circle cx="17.5" cy="19" r="1.8"/></svg>',
}


SERVICES = [
    {
        "code": "H",
        "slug": "housekeeping",
        "icon": "broom",
        "name": "Housekeeping Services",
        "desc": "Daily upkeep and cleaning for offices and commercial spaces.",
        "detail": "Daily sweeping, mopping, dusting, washroom upkeep and waste management, carried out on a schedule that fits your working hours and doesn't disrupt your team."
    },

    {
        "code": "PC",
        "slug": "pest-control",
        "icon": "bug",
        "name": "Pest Control Services",
        "desc": "Scheduled treatments to keep premises pest-free.",
        "detail": "Routine, safe pest-control treatments for offices, pantries and storage areas, with a visit schedule agreed up front and documented after every service."
    },

    {
        "code": "S",
        "slug": "security",
        "icon": "shield",
        "name": "Security Services",
        "desc": "Trained guards and access control for corporate premises.",
        "detail": "Trained, uniformed security personnel for entry management, patrolling and visitor control, staffed to match your site's shift pattern."
    },

    {
        "code": "PM",
        "slug": "payroll-management",
        "icon": "chart",
        "name": "Payroll Management",
        "desc": "Accurate, on-time payroll handling for deployed staff.",
        "detail": "End-to-end payroll processing for deployed staff — attendance, statutory compliance and disbursal — handled so it's one less thing for your HR team to track."
    },

    {
        "code": "P",
        "slug": "pantry-office-boy",
        "icon": "cup",
        "name": "Pantry & Office Boy Services",
        "desc": "Day-to-day pantry running and general office support staff.",
        "detail": "Dependable pantry staff and office assistants for tea/coffee service, courier handling, and the everyday errands that keep an office moving."
    },

    {
        "code": "CS",
        "slug": "corporate-staffing",
        "icon": "users",
        "name": "Corporate Staffing",
        "desc": "Reliable manpower sourcing across facility roles.",
        "detail": "Vetted manpower across facility roles, sourced and deployed quickly so you're never short-staffed at a site."
    },

    {
        "code": "F",
        "slug": "facade-cleaning",
        "icon": "building",
        "name": "Facade Cleaning",
        "desc": "Exterior and high-rise building facade maintenance.",
        "detail": "Trained crews and rigged access for exterior and high-rise facade cleaning, carried out with full safety protocols."
    },

    {
        "code": "MH",
        "slug": "material-handling",
        "icon": "truck",
        "name": "Material Handling",
        "desc": "Safe, organised handling and movement of materials on site.",
        "detail": "Organised loading, moving and storage of materials on site, with trained handling staff to reduce damage and downtime."
    },
]


for _s in SERVICES:
    _s["icon_svg"] = Markup(ICONS[_s["icon"]])


SERVICES_BY_SLUG = {
    s["slug"]: s for s in SERVICES
}


@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year
    }


# ----------------------------------------------------------------------
# Public pages
# ----------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        active="home",
        services=SERVICES
    )


@app.route("/services")
def services():
    return render_template(
        "services.html",
        active="services",
        services=SERVICES
    )


@app.route("/services/<slug>", methods=["GET", "POST"])
def service_detail(slug):

    service = SERVICES_BY_SLUG.get(slug)

    if not service:
        flash(
            "That service could not be found.",
            "error"
        )
        return redirect(
            url_for("services")
        )

    def render_this(
        extra_flash=None,
        category="error"
    ):

        if extra_flash:
            flash(
                extra_flash,
                category
            )

        session_user_name = None

        if session.get("user_id"):
            u = _require_user()
            session_user_name = (
                u["name"] if u else None
            )

        return render_template(
            "service_detail.html",
            active="services",
            service=service,
            all_services=SERVICES,
            session_user_name=session_user_name,
        )

    if request.method == "POST":

        if not session.get("user_id"):
            flash(
                "Please log in to request staff for this service.",
                "error"
            )

            return redirect(
                url_for(
                    "login",
                    next=url_for(
                        "service_detail",
                        slug=slug
                    )
                )
            )

        user = _require_user()

        staff_count = request.form.get(
            "staff_count",
            ""
        ).strip()

        site = request.form.get(
            "site",
            ""
        ).strip()

        needed_from = request.form.get(
            "needed_from",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if (
            not staff_count
            or not staff_count.isdigit()
            or int(staff_count) < 1
        ):
            return render_this(
                "Please enter how many staff you need (a number of 1 or more)."
            )

        requests_col.insert_one({
            "user_id": user["_id"],
            "user_name": user["name"],
            "user_email": user["email"],
            "company": user.get("company", ""),
            "service_slug": service["slug"],
            "service_name": service["name"],
            "staff_count": int(staff_count),
            "site": site,
            "needed_from": needed_from,
            "notes": notes,
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        })

        flash(
            f"Your request for {staff_count} staff under {service['name']} has been sent. We'll confirm shortly.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_this()


@app.route("/about")
def about():
    return render_template(
        "about.html",
        active="about"
    )


@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        enquiry = {
            "name": request.form.get(
                "name",
                ""
            ).strip(),

            "company": request.form.get(
                "company",
                ""
            ).strip(),

            "phone": request.form.get(
                "phone",
                ""
            ).strip(),

            "email": request.form.get(
                "email",
                ""
            ).strip(),

            "message": request.form.get(
                "message",
                ""
            ).strip(),

            "created_at": datetime.now(timezone.utc),
        }

        if (
            not enquiry["name"]
            or not enquiry["phone"]
            or not enquiry["email"]
        ):
            flash(
                "Please fill in your name, phone and email.",
                "error"
            )

            return render_template(
                "contact.html",
                active="contact"
            )

        enquiries_col.insert_one(
            enquiry
        )

        flash(
            "Thanks — your enquiry has been sent. We'll be in touch shortly.",
            "success"
        )

        return redirect(
            url_for("contact")
        )

    return render_template(
        "contact.html",
        active="contact"
    )


# ----------------------------------------------------------------------
# Client (user) auth
# ----------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    next_url = (
        request.values.get("next")
        or url_for("dashboard")
    )

    if not next_url.startswith("/"):
        next_url = url_for("dashboard")

    if session.get("user_id"):
        return redirect(next_url)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        company = request.form.get(
            "company",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if (
            not name
            or not email
            or len(password) < 6
        ):
            flash(
                "Please fill in all required fields (password min 6 characters).",
                "error"
            )

            return render_template(
                "register.html",
                active="register",
                next=next_url
            )

        if users_col.find_one(
            {"email": email}
        ):
            flash(
                "An account with that email already exists. Please log in.",
                "error"
            )

            return redirect(
                url_for(
                    "login",
                    next=next_url
                )
            )

        users_col.insert_one({
            "name": name,
            "company": company,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now(timezone.utc),
        })

        flash(
            "Account created. Please log in.",
            "success"
        )

        return redirect(
            url_for(
                "login",
                next=next_url
            )
        )

    return render_template(
        "register.html",
        active="register",
        next=next_url
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    next_url = (
        request.values.get("next")
        or url_for("dashboard")
    )

    if not next_url.startswith("/"):
        next_url = url_for("dashboard")

    if session.get("user_id"):
        return redirect(next_url)

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = users_col.find_one(
            {"email": email}
        )

        if (
            user
            and check_password_hash(
                user["password_hash"],
                password
            )
        ):
            session.clear()

            session["user_id"] = str(
                user["_id"]
            )

            flash(
                f"Welcome back, {user['name']}.",
                "success"
            )

            return redirect(next_url)

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "login.html",
        active="login",
        next=next_url
    )


@app.route("/logout")
def logout():

    session.pop(
        "user_id",
        None
    )

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


def _require_user():

    uid = session.get("user_id")

    if not uid:
        return None

    return users_col.find_one(
        {
            "_id": ObjectId(uid)
        }
    )


@app.route("/dashboard")
def dashboard():

    user = _require_user()

    if not user:
        flash(
            "Please log in to view your account.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    enquiries = list(
        enquiries_col.find(
            {
                "email": user["email"]
            }
        ).sort(
            "created_at",
            -1
        )
    )

    staff_requests = list(
        requests_col.find(
            {
                "user_id": user["_id"]
            }
        ).sort(
            "created_at",
            -1
        )
    )

    return render_template(
        "dashboard.html",
        active="dashboard",
        user=user,
        enquiries=enquiries,
        staff_requests=staff_requests,
    )


# ----------------------------------------------------------------------
# Admin auth
# ----------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_id"):
        return redirect(
            url_for("admin_dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        admin = admins_col.find_one(
            {
                "username": username
            }
        )

        if (
            admin
            and check_password_hash(
                admin["password_hash"],
                password
            )
        ):
            session.clear()

            session["admin_id"] = str(
                admin["_id"]
            )

            session["admin_username"] = (
                admin["username"]
            )

            flash(
                "Welcome back.",
                "success"
            )

            return redirect(
                url_for("admin_dashboard")
            )

        flash(
            "Invalid admin username or password.",
            "error"
        )

    return render_template(
        "admin/login.html",
        active="admin_login"
    )


@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_id",
        None
    )

    session.pop(
        "admin_username",
        None
    )

    flash(
        "Admin logged out.",
        "success"
    )

    return redirect(
        url_for("index")
    )


def _require_admin():
    return bool(
        session.get("admin_id")
    )


@app.route("/admin")
def admin_dashboard():

    if not _require_admin():
        flash(
            "Please log in as admin.",
            "error"
        )

        return redirect(
            url_for("admin_login")
        )

    users = list(
        users_col.find().sort(
            "created_at",
            -1
        )
    )

    enquiries = list(
        enquiries_col.find().sort(
            "created_at",
            -1
        )
    )

    staff_requests = list(
        requests_col.find().sort(
            "created_at",
            -1
        )
    )

    total_staff_requested = sum(
        r.get("staff_count", 0)
        for r in staff_requests
    )

    return render_template(
        "admin/dashboard.html",
        active="admin_dashboard",
        users=users,
        enquiries=enquiries,
        staff_requests=staff_requests,
        user_count=len(users),
        enquiry_count=len(enquiries),
        request_count=len(staff_requests),
        total_staff_requested=total_staff_requested,
    )


# ----------------------------------------------------------------------
# CLI helper: create the first admin account
#
# flask --app app.py create-admin
# ----------------------------------------------------------------------

@app.cli.command("create-admin")
def create_admin():

    import getpass

    username = input(
        "Admin username: "
    ).strip().lower()

    if admins_col.find_one(
        {
            "username": username
        }
    ):
        print(
            "An admin with that username already exists."
        )
        return

    password = getpass.getpass(
        "Admin password: "
    )

    confirm = getpass.getpass(
        "Confirm password: "
    )

    if password != confirm:
        print(
            "Passwords did not match. Try again."
        )
        return

    admins_col.insert_one({
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc),
    })

    print(
        f"Admin '{username}' created."
    )


# ----------------------------------------------------------------------
# One-time web admin bootstrap
# ----------------------------------------------------------------------

@app.route(
    "/setup-admin",
    methods=["GET", "POST"]
)
def setup_admin():

    if admins_col.count_documents({}) > 0:

        flash(
            "An admin account already exists. Please log in normally.",
            "error"
        )

        return redirect(
            url_for("admin_login")
        )

    required_key = os.environ.get(
        "ADMIN_SETUP_KEY"
    )

    if (
        required_key
        and request.values.get("key") != required_key
    ):
        flash(
            "Missing or incorrect setup key.",
            "error"
        )

        return render_template(
            "admin/setup.html",
            active="admin_login",
            key_required=True
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm",
            ""
        )

        if (
            not username
            or len(password) < 6
        ):
            flash(
                "Enter a username and a password of at least 6 characters.",
                "error"
            )

            return render_template(
                "admin/setup.html",
                active="admin_login",
                key_required=bool(required_key)
            )

        if password != confirm:
            flash(
                "Passwords did not match.",
                "error"
            )

            return render_template(
                "admin/setup.html",
                active="admin_login",
                key_required=bool(required_key)
            )

        admins_col.insert_one({
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now(timezone.utc),
        })

        flash(
            f"Admin '{username}' created. You can now log in below.",
            "success"
        )

        return redirect(
            url_for("admin_login")
        )

    return render_template(
        "admin/setup.html",
        active="admin_login",
        key_required=bool(required_key)
    )


# ----------------------------------------------------------------------
# Run application
# ----------------------------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        debug=True,
        host="0.0.0.0",
        port=port
    )
