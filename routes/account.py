from pickle import dumps, loads
from base64 import b64encode, b64decode
import json
from uuid import uuid4

from bcrypt import gensalt, hashpw, checkpw
from flask_login import login_required, current_user
from flask import redirect, flash, render_template, request, Response, g, make_response

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
    else:
        with Session() as session:
            current_user.profile_image = get_base64_image_blob(
                form.url.data).encode()
            session.merge(current_user)
            session.commit()

    return redirect('/account')


@app.route('/account', methods=['POST'])
@login_required
def update_account():
    form = AccountForm(request.form)

    if not form.validate():
        flash(json.dumps(form.errors), 'error')
    else:
        with Session() as session:
            # - If the user changes email or password,
            # they must enter their current password correctly.

            # - Email change is only allowed if
            # the new address is not used by another account.

            # - Password is changed only if
            # a new password is provided and confirmed.

            # - The is_admin flag is never updated here;
            # role changes are restricted to a separate admin-only interface.

            new_email = form.email.data
            old_password = form.old_password.data
            new_password = form.password.data
            new_password_confirm = form.password_control.data

            email_changed = new_email != current_user.email
            password_change_requested = bool(new_password)

            if email_changed or password_change_requested:
                if not old_password:
                    flash("Please enter your current password to update email or password.", "error")
                    return redirect("/account")
                if not checkpw(
                        old_password.encode("utf-8"),
                        current_user.password.encode("utf-8"),
                    ):
                    flash("Current password is incorrect.", "error")
                    return redirect("/account")

                if email_changed:
                    existing = (
                        session.query(User)
                        .filter(User.email == form.email.data)
                        .first()
                    )

                    if existing and existing.id != current_user.id:
                        flash("This email address is already in use by another account.", "error")
                        return redirect("/account")

                current_user.email = form.email.data

                if password_change_requested:
                    if new_password != new_password_confirm:
                        flash("New passwords do not match.", "error")
                        return redirect("/account")

                    current_user.password = hashpw(
                            new_password.encode("utf-8"), gensalt()
                        ).decode("utf-8")

                session.merge(current_user)
                session.commit()
                flash('Account updated', 'success')

    return redirect('/account')

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


@app.route('/darkmode', methods=['POST'])
def toggle_darkmode():
    response = make_response(redirect('/account'))

    preferences = g.preferences
    preferences['mode'] = 'light' if preferences['mode'] == 'dark' else 'dark'

    response.set_cookie('preferences', b64encode(dumps(preferences)).decode())
    return response


default_preferences = {'mode': 'light'}


@app.before_request
def before_request():
    preferences = request.cookies.get('preferences')
    if preferences is None:
        preferences = default_preferences
    else:
        preferences = loads(b64decode(preferences))

    g.preferences = preferences


@app.after_request
def after_request(response: Response) -> Response:
    if request.cookies.get('preferences') is None:
        preferences = default_preferences
        response.set_cookie('preferences',
                            b64encode(dumps(preferences)).decode())
    return response
