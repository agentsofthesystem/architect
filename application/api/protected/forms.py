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
from wtforms.widgets import TextArea

from application.api.controllers import friends
from application.api.controllers import groups
from application.models.user import UserSql


class AccountProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])

    email = StringField("Email", validators=[DataRequired()])

    hidden_email = HiddenField("Hidden Email")
    verified = HiddenField("Verified")


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


class GroupMessageForm(FlaskForm):
    subject = StringField("Subject", validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired()])
    method = HiddenField("PATCH")
    group_id = HiddenField("Group", validators=[DataRequired()])
    send = SubmitField("Send")


class NewAgentForm(FlaskForm):
    owner_id = HiddenField("Owner User ID")
    method = HiddenField("POST")

    name = StringField("Name", validators=[DataRequired()])
    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    ssl_public_cert = StringField(
        "SSL Public Certificate", widget=TextArea(), validators=[DataRequired()]
    )
    access_token = StringField("Access Token", validators=[DataRequired()])
    send = SubmitField("Send")


class UpdateAgentForm(FlaskForm):
    agent_id = HiddenField("Agent ID")
    method = HiddenField("PATCH")

    name = StringField("Name", validators=[DataRequired()])
    hostname = StringField("Hostname", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    ssl_public_cert = StringField(
        "SSL Public Certificate", widget=TextArea(), validators=[DataRequired()]
    )
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
def _populate_friend_choices() -> list:
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


@staticmethod
def _populate_group_choices() -> list:
    choices = []

    # Explicitly want to use == for condition.
    if current_user == None:  # noqa: E711
        return choices

    group_list = groups.get_owned_groups() + groups.get_associated_groups()

    # TODO - Eliminate groups that already belong to a given agent via kwarg.
    for group in group_list:
        owner_obj = UserSql.query.filter_by(user_id=group["owner_id"]).first()
        label = f"{group['name']} ({owner_obj.username})"
        choices.append((group["group_id"], label))

    return choices


class AddFriendToGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    method = HiddenField("PATCH_FRIEND")
    friends_list = SelectMultipleField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_friend_choices()


class InviteFriendToGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    requestor_id = HiddenField("Requestor ID")
    method = HiddenField("PATCH_INVITE_FRIEND")
    friends_list = SelectField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_friend_choices()


class TransferGroupForm(FlaskForm):
    group_id = HiddenField("Group ID")
    method = HiddenField("PATCH_GROUP_TRANSFER")
    friends_list = SelectField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_friend_choices()


class ShareAgentToGroupForm(FlaskForm):
    agent_id = HiddenField("Group ID")
    method = HiddenField("SHARE_TO_GROUP")
    group_list = SelectField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.group_list.choices = _populate_group_choices()


class ShareAgentToFriendForm(FlaskForm):
    agent_id = HiddenField("Group ID")
    method = HiddenField("SHARE_TO_FRIEND")
    friends_list = SelectField(choices=[], validators=[DataRequired()])

    def populate_choices(self) -> list:
        self.friends_list.choices = _populate_friend_choices()
