from wtforms import Form, PasswordField, EmailField, validators

# The is_admin flag is intentionally NOT exposed here to prevent privilege escalation.
class AccountForm(Form):
    email = EmailField(
        "Email Address",
        [
            validators.DataRequired(message="Email address is required."),
            validators.Email(message="Please enter a valid email address."),
        ],
    )
    old_password = PasswordField("Current Password")
    password = PasswordField(
        "New Password",
        [
            validators.Optional(),
            validators.Length(
                min=8,
                message="New password must be at least 8 characters long.",
            ),
        ],
    )
    password_control = PasswordField(
        "Confirm New Password",
        [
            validators.Optional(),
            validators.EqualTo(
                "password",
                message="New passwords must match.",
            ),
        ],
    )
