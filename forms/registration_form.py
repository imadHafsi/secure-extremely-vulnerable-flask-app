from wtforms import Form, StringField, PasswordField, EmailField, validators


class RegistrationForm(Form):
    email = EmailField(
        "Email Address",
        [
            validators.DataRequired(message="Email address is required."),
            validators.Email(message="Please enter a valid email address."),
        ],
    )
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(message="Password is required."),
            validators.Length(
                min=8,
                message="Password must be at least 8 characters long.",
            ),
        ],
    )
    registration_code = StringField(
        "Registration Code",
        [
            validators.DataRequired(message="Registration code is required."),
            validators.Length(
                min=5,
                message="Registration code must be at least 5 characters long.",
            ),
        ],
    )