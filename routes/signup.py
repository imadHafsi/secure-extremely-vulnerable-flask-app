from json import dumps
from sqlite3 import OperationalError
from typing import Union
from flask import render_template, request, redirect, flash
from bcrypt import gensalt, hashpw
from app import app
from models import Session, User, RegistrationCode
from forms.registration_form import RegistrationForm

def validate_token(code: str, session: Session) -> Union[str, None]:
    try:
        
        token = (
        session.query(RegistrationCode)
        .filter(RegistrationCode.code == code)
        .first()
        )

        if token is None:
            return None

        return token.id
    except OperationalError:
        return None
    
@app.route('/signup', methods=['GET'])
def signup():
    form = RegistrationForm()
    return render_template("signup.html", form=form)

@app.route("/signup", methods=["POST"])
def do_signup():
    form = RegistrationForm(request.form)

    if not form.validate():
        # Show per-field error messages
        for field_name, errors in form.errors.items():
            field_label = getattr(form, field_name).label.text
            for error in errors:
                flash(f"{field_label}: {error}", "error")
        return redirect("/signup")

    with Session() as session:
        # Check if user already exists
        user_already_exists = session.query(
            session.query(User)
            .filter(User.email == form.email.data)
            .exists()
        ).scalar()

        if user_already_exists:
            flash("A user with that email already exists.", "warning")
            return redirect("/signup")

        # Validate registration code
        code = form.registration_code.data
        token_id = validate_token(code, session)
        if token_id is None:
            flash("Invalid registration code.", "warning")
            return redirect("/signup")

        token = session.get(RegistrationCode, token_id)
        if token.code != code:
            flash("Unexpected registration code mismatch.", "error")
            return redirect("/signup")

        # Consume the registration code
        session.delete(token)

        
        user = User(
            form.email.data,
            hashpw(form.password.data.encode("utf-8"), gensalt()).decode("utf-8"),
        )

        session.add(user)
        session.commit()
        flash("Account created successfully. You can now log in.", "success")

    return redirect("/home")
