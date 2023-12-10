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


class GlobalMessageForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    send = SubmitField("Send")


class DirectMessageForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    recipient_id = IntegerField("Recipient", validators=[DataRequired()])
    send = SubmitField("Send")


class NewAgentForm(FlaskForm):
    owner_id = HiddenField("Owner User ID")
    method = HiddenField("POST")

    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    access_token = StringField("Access Token", validators=[DataRequired()])
    send = SubmitField("Send")


class UpdateAgentForm(FlaskForm):
    agent_id = HiddenField("Agent ID")
    method = HiddenField("PATCH")

    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    access_token = StringField("Access Token", validators=[DataRequired()])

    send = SubmitField("Send")
