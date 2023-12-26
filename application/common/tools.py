"""Common Tools Go Here."""
import os
import sys

from functools import wraps

from flask import flash, redirect, url_for, current_app
from flask_admin import AdminIndexView, expose
from flask_login import current_user


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


def verified_required(func):
    """Define Decorate to enforce verified users for routes."""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.verified is False:
            flash("You must first verify your email address!", "danger")
            return redirect(url_for("protected.account"))
        else:
            return func(*args, **kwargs)

    return decorated_view


def subscription_required(func):
    """Define Decorate to enforce verified users for routes."""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        # Only if payments are enabled and user subscribed.
        if current_user.subscribed is False and current_app.config["APP_ENABLE_PAYMENTS"]:
            flash("You must be a paying user to access this page!", "danger")
            return redirect(url_for("protected.account", tab="billing"))
        else:
            return func(*args, **kwargs)

    return decorated_view


def admin_required(func):
    """Define Decorate to enforce verified users for routes."""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not hasattr(current_user, "admin") and not current_user.is_authenticated:
            flash("You must be a site administrator to access this page!", "danger")
            return redirect(url_for("public.signin", tab="account"))
        elif not hasattr(current_user, "admin") and current_user.is_authenticated:
            flash("You must be a site administrator to access this page!", "danger")
            return redirect(url_for("protected.account", tab="account"))
        elif current_user.admin is False:
            flash("You must be a site administrator to access this page!", "danger")
            return redirect(url_for("protected.account", tab="account"))
        else:
            return func(*args, **kwargs)

    return decorated_view


def check_password(password):
    if len(password) < 7:
        return False

    return True


@staticmethod
def _get_application_path():
    if getattr(sys, "frozen", False):
        application_path = os.path.join(sys._MEIPASS, "application")
    elif __file__:
        current_file = os.path.abspath(__file__)
        application_path = os.path.dirname(os.path.dirname(current_file))
    return application_path


@staticmethod
def _get_setting(setting_name: str, setting_objs: list):
    setting_value = None
    for setting in setting_objs:
        if setting.name == setting_name:
            setting_value = setting.value
    return setting_value


@staticmethod
def format_url(input: str) -> str:
    hostname = input

    if "http://" not in input or "https://" not in input:
        hostname = f"http://{input}"

    return hostname
