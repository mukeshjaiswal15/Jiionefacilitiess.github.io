# Jii One Facilities — Website

A classic corporate website for **Jii One Facilities**, built from the
content on your business card: services, contact details, and the
Director's profile. It works on both laptop/PC and mobile screens.

Stack:
- **Backend:** Python (Flask)
- **Database:** MongoDB (via `pymongo`)
- **Frontend:** server-rendered HTML + CSS (no build step needed)
- **Auth:** two separate logins — a client/user login and a staff/admin login

---

## 1. Install prerequisites

- Python 3.9+
- MongoDB running locally (or an Atlas connection string)

Install MongoDB Community Edition (if you don't already have it) from
https://www.mongodb.com/try/download/community, or use a free
MongoDB Atlas cluster and copy its connection string.

## 2. Set up the project

```bash
cd jiione_website
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configure environment variables (optional but recommended)

```bash
export SECRET_KEY="a-long-random-string"
export MONGO_URI="mongodb://localhost:27017"     # or your Atlas URI
export MONGO_DBNAME="jiione_facilities"
```

On Windows (PowerShell):
```powershell
$env:SECRET_KEY="a-long-random-string"
$env:MONGO_URI="mongodb://localhost:27017"
$env:MONGO_DBNAME="jiione_facilities"
```

If you skip this step the app falls back to `localhost:27017` and a
default (insecure) secret key — fine for trying it out locally, but
change both before putting this on the internet.

## 4. Create your first admin account

The admin login is separate from client accounts, stored in its own
`admins` collection, so a customer can never sign in as staff.

```bash
flask --app app.py create-admin
```

You'll be prompted for a username and password. Run this once per
admin you want to add.

## 5. Run the site

```bash
flask --app app.py run
```

Then open **http://localhost:5000** in your browser.

- Client site & login: `http://localhost:5000/login`
- Admin login: `http://localhost:5000/admin/login`

## What's included

- **Home, Services, About, Contact** pages built from your business
  card's content (all 8 service lines, address, phone numbers, email,
  Director's name/title).
- **Contact form** that saves each enquiry into the `enquiries`
  MongoDB collection.
- **Client accounts** — visitors can register/log in and see a simple
  dashboard with their own enquiries.
- **Admin dashboard** — after admin login, staff can see every
  registered client and every enquiry submitted through the site.
- Passwords are never stored in plain text (hashed with Werkzeug's
  `generate_password_hash`).

## Project structure

```
jiione_website/
├── app.py                  # Flask app, routes, MongoDB access
├── requirements.txt
├── templates/
│   ├── base.html            # shared header/nav/footer
│   ├── index.html, services.html, about.html, contact.html
│   ├── login.html, register.html, dashboard.html
│   └── admin/
│       ├── login.html
│       └── dashboard.html
└── static/
    └── css/style.css        # all styling
```

## Notes for going live

- Set a strong, random `SECRET_KEY`.
- Use a production WSGI server (e.g. `gunicorn app:app`) behind Nginx
  rather than Flask's built-in dev server.
- Point `MONGO_URI` at a properly secured MongoDB instance (Atlas with
  IP allow-listing, or a self-hosted instance with auth enabled).
- Serve the site over HTTPS.
