from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (
    HiddenField,
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    IntegerField,
    SelectField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired

from application.api.controllers import friends


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

    name = StringField("Name", validators=[DataRequired()])
    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    access_token = StringField("Access Token", validators=[DataRequired()])
    send = SubmitField("Send")


class UpdateAgentForm(FlaskForm):
    agent_id = HiddenField("Agent ID")
    method = HiddenField("PATCH")

    name = StringField("Name", validators=[DataRequired()])
    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    access_token = StringField("Access Token", validators=[DataRequired()])

    send = SubmitField("Send")


class FriendRequestForm(FlaskForm):
    friend_code = StringField("Friend Code", validators=[DataRequired()])

    send = SubmitField("Send")


class NewGroupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    method = HiddenField("POST")
    send = SubmitField("Send")


class UpdateGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    name = StringField("Name", validators=[DataRequired()])
    method = HiddenField("PATCH")
    send = SubmitField("Send")


@staticmethod
def _populate_choices() -> list:
    choices = []

    # Explicitly want to use == for condition.
    if current_user == None:  # noqa: E711
        return choices

    friend_list = friends.get_my_friends()

    for friend in friend_list:
        if current_user.user_id == friend["initiator_id"]:
            choices.append((friend["receiver"]["user_id"], friend["receiver"]["username"]))
        else:
            choices.append((friend["initiator"]["user_id"], friend["initiator"]["username"]))

    return choices


class AddFriendToGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    method = HiddenField("PATCH_FRIEND")
    friends_list = SelectMultipleField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_choices()


class TransferGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    method = HiddenField("PATCH_GROUP_TRANSFER")
    friends_list = SelectField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_choices()
