from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, BooleanField
from wtforms.validators import DataRequired


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])


class ResetPasswordForm(FlaskForm):
    token = HiddenField("token")

    password = PasswordField("Password", validators=[DataRequired()])

    password2 = PasswordField("Confirm Password", validators=[DataRequired()])


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])

    email = StringField("Email", validators=[DataRequired()])

    password = PasswordField("Password", validators=[DataRequired()])


class SignInForm(FlaskForm):
    email = StringField("Username")

    password = PasswordField("Password", validators=[DataRequired()])

    remember = BooleanField("Remember")
