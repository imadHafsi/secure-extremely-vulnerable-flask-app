import json
from uuid import uuid4

from bcrypt import gensalt, hashpw, checkpw
from flask_login import login_required, current_user
from flask import redirect, flash, render_template, request, Response, g

from app import app
from models import Session, Note, User
from forms.image_form import ImageForm
from forms.account_form import AccountForm
from utils.profile_image import get_base64_image_blob



@app.route('/account')
@login_required
def account():
    return render_template('account.html', uuid=str(uuid4()))


@app.route('/search')
@login_required
def search():
    search_param = request.args.get('search', '')
    with Session() as session:
        session.query(Note)

        personal_notes = (
            session.query(Note)
            .filter(
                Note.user_id == current_user.id,
                Note.text.like(f"%{search_param}%")
            )
            .all()
        )
        return render_template(
            'search.html',
            search=search_param,
            personal_notes=personal_notes,
        )


@app.route('/accounts/notes')
@login_required
def get_personal_notes():

    with Session() as session:
        personal_notes = session.query(Note).filter(
            Note.user_id == current_user.id).all()
        return render_template('personal_notes.html',
                               personal_notes=personal_notes)


@app.route('/account/image', methods=['POST'])
@login_required
def add_image():
    form = ImageForm(request.form)

    if not form.validate():
        flash(json.dumps(form.errors), 'error')
        return redirect('/account')

    try:
        image_blob = get_base64_image_blob(form.url.data)
    except ValueError as e:
        # Our own safety checks (unsafe URL, not an image, too large, etc.)
        flash(str(e), 'error')
        return redirect('/account')
    except Exception:
        # Any unexpected error while fetching/parsing the image
        flash("Could not download profile image from that URL.", "error")
        return redirect('/account')

    with Session() as session:
        current_user.profile_image = image_blob.encode()
        session.merge(current_user)
        session.commit()
        flash("Profile image updated.", "success")

    return redirect('/account')


@app.route("/account", methods=["POST"])
@login_required
def update_account():
    form = AccountForm(request.form)

    if not form.validate():
        # Show each field error as a readable flash message
        for field_name, errors in form.errors.items():
            field_label = getattr(form, field_name).label.text
            for error in errors:
                flash(f"{field_label}: {error}", "error")
        return redirect("/account")

    new_email = form.email.data
    old_password = form.old_password.data
    new_password = form.password.data

    email_changed = new_email != current_user.email
    password_change_requested = bool(new_password)

    with Session() as session:
        # If the user changes email or password,
        # they must enter their current password correctly.
        if email_changed or password_change_requested:
            if not old_password:
                flash(
                    "Please enter your current password to update email or password.",
                    "error",
                )
                return redirect("/account")

            if not checkpw(
                old_password.encode("utf-8"),
                current_user.password.encode("utf-8"),
            ):
                flash("Current password is incorrect.", "error")
                return redirect("/account")

        # Email change is only allowed if the new address is not used by another account.
        if email_changed:
            existing = (
                session.query(User)
                .filter(User.email == new_email)
                .first()
            )
            if existing and existing.id != current_user.id:
                flash(
                    "This email address is already in use by another account.",
                    "error",
                )
                return redirect("/account")

            current_user.email = new_email

        # Password is changed only if a new password is provided and confirmed.
        if password_change_requested:
            # form.validate() already ensured length + EqualTo (match)
            # Optional extra: new password must differ from old password
            if checkpw(
                new_password.encode("utf-8"),
                current_user.password.encode("utf-8"),
            ):
                flash(
                    "New password must be different from the old password.",
                    "error",
                )
                return redirect("/account")

            current_user.password = hashpw(
                new_password.encode("utf-8"),
                gensalt(),
            ).decode("utf-8")


        session.merge(current_user)
        session.commit()
        flash("Account updated", "success")

    return redirect("/account")

@app.route("/admin/users")
@login_required
def admin_list_users():

    if not current_user.is_admin:
        flash("You are not authorised to view that page.", "error")
        return redirect("/home")

    with Session() as session:
        users = session.query(User).all()

    return render_template("admin_users.html", users=users)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@login_required
def admin_update_user_role(user_id: int):

    if not current_user.is_admin:
        flash("You are not authorised to change user roles.", "error")
        return redirect("/home")

    make_admin = request.form.get("is_admin") == "on"

    with Session() as session:
        user = session.get(User, user_id)
        if user is None:
            flash("User not found.", "warning")
            return redirect("/admin/users")

        # prevent the admins from demoting themselves
        if user.id == current_user.id and not make_admin:
            flash("You cannot remove your own admin role here.", "error")
            return redirect("/admin/users")

        user.is_admin = make_admin
        session.commit()
        flash("User role updated.", "success")

    return redirect("/admin/users")

default_preferences = {"mode": "light"}


@app.route("/darkmode", methods=["POST"])
@login_required
def toggle_darkmode():

    prefs = getattr(g, "preferences", default_preferences.copy())
    mode = prefs.get("mode", "light")

    prefs["mode"] = "light" if mode == "dark" else "dark"
    g.preferences = prefs

    return redirect("/account")


@app.before_request
def before_request():

    raw = request.cookies.get("preferences")
    if not raw:
        # start from a copy so each request gets its own dict
        preferences = default_preferences.copy()
    else:
        try:
            preferences = json.loads(raw)
        except json.JSONDecodeError:
            preferences = default_preferences.copy()

    # Basic validation: only allow known modes
    mode = preferences.get("mode", "light")
    if mode not in ("light", "dark"):
        preferences["mode"] = "light"

    g.preferences = preferences


@app.after_request
def after_request(response: Response) -> Response:

    prefs = getattr(g, "preferences", None)
    if prefs is None:
        prefs = default_preferences.copy()

    response.set_cookie(
        "preferences",
        json.dumps(prefs),
        httponly=False,
        samesite="Lax",
    )
    return response
