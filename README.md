# Secure Extremely Vulnerable Flask App (SEVFA)

A security-hardened version of the **Extremely Vulnerable Flask App (EVFA)** — a small Flask/SQLAlchemy note‑taking web application built for learning secure web development.

This repository keeps the original feature set (registration/login, notes CRUD + search, profile image by URL, UI preferences, admin role + registration code management) while refactoring high‑risk areas to mitigate common OWASP Top 10 issues such as **SQL injection, broken access control (IDOR), stored XSS, CSRF, insecure deserialization, SSRF, and insecure configuration**.


---

## Features

### Core functionality
- **Invite-based signup** using registration codes
- **User authentication** (login/logout) and session management
- **Notes management**
  - Create, view, edit, delete notes
  - Private / shared notes (depending on `private` flag usage in the app)
  - Search notes
- **Account management**
  - Update account details
  - Set profile image via URL
  - Toggle UI light/dark mode preference (cookie-backed)
- **Admin functionality**
  - Manage registration codes
  - Manage user roles (admin/non-admin)

### Security objectives (what was improved)
- Prevent **SQL injection** by replacing unsafe SQL string building with **SQLAlchemy ORM filters**
- Enforce **authorization** (ownership checks) to mitigate **IDOR / horizontal privilege escalation**
- Prevent **stored XSS** using server-side **HTML sanitization** for note content
- Enable **CSRF protection** across state-changing routes using **Flask‑WTF CSRF**
- Remove **insecure deserialization** by replacing `pickle` cookies with **validated JSON**
- Reduce **SSRF** risk in profile image download using:
  - scheme/host validation
  - private IP / loopback blocking
  - content-type checks, timeouts, and size limits
- Improve **secure configuration** by moving secrets to environment variables and avoiding debug leakage

---

## Project structure

```
.
├─ app.py                     # Flask app setup, CSRF, error handling, route init
├─ config.py                  # Environment-driven configuration (SECRET_KEY, DATABASE_URL)
├─ db_seed.py                 # Development-only seeding (users + codes + sample notes)
├─ requirements.txt           # Python dependencies
├─ Dockerfile                 # Container build
├─ docker-compose.yml         # Compose run configuration
├─ uwsgi.ini                  # uWSGI config (optional)
│
├─ routes/                    # Flask routes / controllers
│  ├─ home.py                 # Landing / home pages
│  ├─ login.py                # Login/logout routes
│  ├─ signup.py               # Invite-based signup
│  ├─ notes.py                # Notes CRUD endpoints
│  ├─ account.py              # Account settings, preferences cookie, admin user mgmt routes
│  └─ registration_codes.py   # Admin registration code management
│
├─ forms/                     # Flask‑WTF forms + validators
│  ├─ login_form.py
│  ├─ registration_form.py
│  ├─ note_form.py
│  ├─ account_form.py
│  └─ image_form.py
│
├─ models/                    # SQLAlchemy models + DB session/engine
│  ├─ base_model.py
│  ├─ user.py
│  ├─ note.py
│  └─ registration_code.py
│
├─ utils/                     # Security helpers and shared logic
│  ├─ sanitizer.py            # HTML allowlist sanitization for notes (Bleach)
│  ├─ profile_image.py        # Hardened image fetcher with SSRF defenses
│  └─ notes.py                # Note query helpers
│
├─ templates/                 # Jinja2 templates
├─ static/                    # CSS/images/icons
└─ conf/nginx.conf            # Optional Nginx config
```

---

## Setup and installation

### 1) Clone
```bash
git clone https://github.com/imadHafsi/secure-extremely-vulnerable-flask-app.git
cd secure-extremely-vulnerable-flask-app
```

### 2) Python (virtualenv)

#### Windows (PowerShell)
```powershell
py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Environment variables

At minimum, set a strong `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```


#### Windows (PowerShell)
```powershell
$env:SECRET_KEY = "<GENERATED_KEY>"
$env:FLASK_APP = "app.py"
# Optional:
# $env:DATABASE_URL = "sqlite:///D:/full/path/to/database.db"
# $env:SQL_ECHO = "true"
$env:SEVFA_ENV = "development"   # seed runs
# $env:SEVFA_ENV = "production"  # seed skipped
```


### 4) Run
```bash
flask run
```

Then open:
- `http://localhost:5000`


---

## Usage guide

1. **Get a registration code**  
   - In development, the seed can create sample registration codes and users.
   - In production-like mode, seeding is skipped, so you must create codes/admins via a controlled process.

2. **Sign up**  
   - Go to `/signup`, enter a valid registration code, then create an account.

3. **Log in / log out**  
   - `/login` to sign in
   - `/logout` to end the session

4. **Create and manage notes**
   - Visit `/home` to view  your notes and shared notes from other users
   - Visit `/Account/notes` to view only your notes
   - Create notes (title/text + private flag)
   - Edit and delete notes (deletion requires ownership or admin rights)

5. **Search notes**
   - Use `/search?search=<term>` to search within your notes content.

6. **Account settings**
   - `/account` to manage account details and toggle dark mode
   - Set profile image by URL (the server fetches and embeds it as base64)

7. **Admin operations** (admin users only)
   - `/admin/users` — manage user roles (admin/non-admin)
   - `/registration-codes` — generate/manage signup codes

---

## Security improvements (what changed vs. the original EVFA)

This repository was built by iteratively hardening the original vulnerable app. Key improvements include:

- **Secrets/config moved to environment**
  - `SECRET_KEY` and `DATABASE_URL` are no longer hard-coded.
  - Optional SQL query logging can be toggled via `SQL_ECHO`.

- **SQL injection fixes**
  - Registration code validation and note searching use ORM filters instead of unsafe SQL string concatenation.

- **CSRF protection**
  - Global CSRF protection is enabled and POST forms include CSRF tokens (Flask‑WTF).

- **Stored XSS prevention**
  - Notes are sanitized server-side using a strict allowlist (via `bleach`).

- **Access control + IDOR mitigation**
  - Notes deletion requires note ownership (or admin).
  - Account update actions require authentication.
  - Admin role is managed through a dedicated admin-only route to reduce privilege escalation risk.

- **Insecure deserialization removed**
  - Preferences cookie replaced with JSON, parsed safely and validated (no `pickle.loads` on client data).

- **SSRF hardening for profile images**
  - Blocks loopback/private IP targets, enforces image content types, limits max size, and uses timeouts.

- **Reduced information leakage**
  - Error handling is simplified to avoid revealing internal details in 404 responses.

For a step-by-step view of the changes, see the repository commit history.

---

## Testing process

Security verification combined **manual security tests** and **SAST**:

### Manual checks (examples)
- SQL injection attempts in:
  - registration code validation
  - note search
- Access control tests:
  - try viewing/deleting other users’ notes by changing IDs
  - try role changes as a non-admin
  - prevent an admin from demoting themselves (if implemented)
- XSS tests:
  - store `<script>alert(1)</script>` in a note and confirm it’s sanitized
- CSRF tests:
  - submit POST requests without a CSRF token and confirm rejection
- SSRF tests:
  - attempt `http://127.0.0.1/...` or private IPs as a profile image URL and confirm rejection
  - attempt non-image/oversized responses and confirm rejection

### SAST / linting
- Bandit (example):
  ```bash
  pip install bandit
  bandit -r .
  ```
- Pylint (optional):
  ```bash
  pylint app.py routes models utils forms
  ```

---

## Contributions & references

### Upstream / inspiration
- Original vulnerable app: `manuelz120/extremely-vulnerable-flask-app` (used under its original license)

### Key libraries / frameworks
- Flask, Jinja2
- SQLAlchemy
- Flask-Login
- Flask-WTF (CSRF)
- Bleach (HTML sanitization)
- bcrypt (password hashing)
- Bootstrap-Flask / Flask-CKEditor

### Security guidance referenced
- OWASP Top 10 (2021)
- OWASP Cheat Sheet Series (SQLi, CSRF)
- NIST Secure Software Development Framework (SSDF)

---

## License

This repository is licensed under **GPL-3.0**. See `LICENSE`.
