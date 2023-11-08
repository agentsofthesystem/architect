# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    IntegerField,
)
from wtforms.validators import DataRequired


class AccountProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])

    email = StringField("Email", validators=[DataRequired()])

    hidden_email = HiddenField("Hidden Email")
    verified = HiddenField("Verified")

    first = StringField("First", validators=[DataRequired()])

    last = StringField("Last", validators=[DataRequired()])


class AccountUpdatePasswordForm(FlaskForm):
    hidden_email = HiddenField("Hidden Email")

    verified = HiddenField("Verified")

    current_password = PasswordField("Current Password")

    new_password = PasswordField("New Password")

    repeat_password = PasswordField("Repeat Password")


class StockSearchForm(FlaskForm):
    ticker = StringField("Ticker", validators=[DataRequired()])


class GlobalMessageForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    send = SubmitField("Send")


class DirectMessageForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    recipient_id = IntegerField("Recipient", validators=[DataRequired()])
    send = SubmitField("Send")
