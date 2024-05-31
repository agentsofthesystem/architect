"""Common Tools Go Here."""
import os
import re
import sys
import uuid

from flask import redirect, url_for
from flask_admin import AdminIndexView, expose
from flask_login import current_user

from application.models.friend import Friends


class MyAdminIndexView(AdminIndexView):
    """Define a custom flask admin index view."""

    def __init__(self, url):
        super(MyAdminIndexView, self).__init__(url=url)

    @expose("/")
    def index(self):
        if current_user.is_authenticated:
            if current_user.is_admin:
                return super(MyAdminIndexView, self).index()
            else:
                return redirect(url_for("protected.dashboard"))
        else:
            return redirect(url_for("public.index"))


@staticmethod
def is_valid_email(email: str) -> bool:
    """Check if email is valid."""
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    # pass the regular expression
    # and the string into the fullmatch() method
    if re.fullmatch(regex, email):
        return True
    else:
        return False


@staticmethod
def _get_application_path():
    if getattr(sys, "frozen", False):
        application_path = os.path.join(sys._MEIPASS, "application")
    elif __file__:
        current_file = os.path.abspath(__file__)
        application_path = os.path.dirname(os.path.dirname(current_file))
    return application_path


@staticmethod
def _get_setting(setting_name: str, setting_objs: list) -> str:
    setting_value = None
    for setting in setting_objs:
        if setting.name == setting_name:
            setting_value = setting.value
    return setting_value


@staticmethod
def format_url_prefix(input: str) -> str:
    hostname = input

    # If user somehow put http:// in, update it to https://
    if "http://" in input:
        hostname = hostname.replace("http://", "https://")

    # If just put in the domain name; eg.example.com
    # The add https:// prefix.
    if "http://" not in input and "https://" not in input:
        hostname = f"https://{input}"

    return hostname


@staticmethod
def is_friend(left_side_id, right_side_id) -> bool:
    friend_obj = Friends.query.filter_by(
        initiator_id=left_side_id, receiver_id=right_side_id
    ).first()
    friend_reciprocal_obj = Friends.query.filter_by(
        initiator_id=right_side_id, receiver_id=left_side_id
    ).first()

    # Convert to booleans
    pair_exists = True if friend_obj else False
    reciprocal_pair_exists = True if friend_reciprocal_obj else False

    # If either the pair or reciprocal pair are populated (I.e. Not None) then the two ids are
    # friends.
    return pair_exists or reciprocal_pair_exists


@staticmethod
def generate_friend_code(email: str):
    return uuid.uuid5(uuid.NAMESPACE_DNS, email)
