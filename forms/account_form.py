from wtforms import Form, PasswordField, EmailField


# The is_admin flag is intentionally NOT exposed here to prevent privilege escalation.
class AccountForm(Form):
    email = EmailField('Email Address')
    old_password = PasswordField('Current Password')
    password = PasswordField('Password')
    password_control = PasswordField('Password Control')
