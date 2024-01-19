from flask import flash, redirect, current_app, url_for
from flask_login import current_user
from functools import wraps

from application.api.controllers import agents


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


def agent_permission_required(func):
    """Guards an agent's info endpoint from allowing an un-permissioned user from seeing it."""

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if "agent_id" not in kwargs:
            flash("Missing required input arguments for this decorator.", "danger")
            return redirect(url_for("protected.system_agents"))

        agent_id = kwargs["agent_id"]
        user_id = current_user.user_id

        agent_obj = agents.get_agent_by_id(agent_id, as_obj=True)

        agent_by_association_objs = agents.get_associated_agents()

        warning_msg = "The Architect has not given you permission to access this agent..."

        # if user is owner, return function.
        if agent_obj.owner_id == user_id:
            return func(*args, **kwargs)

        # elif the user has access to any other agents.
        elif len(agent_by_association_objs) > 0:
            is_agent_in_list = False
            # Check that the agent_id provided is in this list.
            for agent in agent_by_association_objs:
                if agent["agent_id"] == agent_id:
                    is_agent_in_list = True

            if is_agent_in_list:
                return func(*args, **kwargs)
            else:
                flash(warning_msg, "warning")
                return redirect(url_for("protected.system_agents"))

        # Catch-all case - user doesn't own the agent and the user isn't associated with any
        # agents.
        else:
            flash(warning_msg, "warning")
            return redirect(url_for("protected.system_agents"))

    return decorated_view
