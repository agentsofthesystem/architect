import jwt

from datetime import datetime, timedelta, timezone
from flask import (
    current_app,
    render_template,
    flash,
)

from flask import session as flask_session
from flask_login import login_user, logout_user, current_user
from kombu.exceptions import OperationalError
from werkzeug.security import generate_password_hash, check_password_hash

from application.api.controllers import agents as agent_control
from application.common import logger, constants, toolbox
from application.extensions import DATABASE, CELERY
from application.models.beta_user import BetaUser
from application.models.setting import SettingsSql
from application.models.user import UserSql
from application.workers.email import send_email


def _get_session_id(session):
    return session["_id"]


def _create_new_user(email: str, password: str = None, oauth_signup: bool = False):
    new_user = UserSql()

    new_user.active = True
    new_user.authenticated = True
    new_user.admin = False

    new_user.username = email.split("@")[0]
    new_user.email = email

    if password:
        new_user.password = generate_password_hash(password)
    else:
        new_user.password = ""

    new_user.friend_code = toolbox.generate_friend_code(email)
    new_user.session_id = _get_session_id(flask_session)
    new_user.last_message_read_time = datetime.now(timezone.utc)

    if oauth_signup:
        new_user.verified = True

    try:
        DATABASE.session.add(new_user)
        DATABASE.session.commit()
    except Exception as error:
        logger.error(error)

    return new_user


def _user_exists(email):
    check_user_obj = UserSql.query.filter_by(email=email).first()

    return False if check_user_obj is None else True


def _handle_sign_in(email: str, password: str = None, remember_me: bool = False):
    is_successful = False

    user_qry = UserSql.query.filter_by(email=email)
    user_obj = user_qry.first()

    if user_obj is None:
        return False

    # If beta mode is enabled, restrict sign-ins.
    beta_mode_enable = SettingsSql.query.filter_by(name="APP_ENABLE_BETA").first()

    if beta_mode_enable.value == "True" or beta_mode_enable.value == "true":
        # Only allowed and active beta users.
        # Does not apply to the site admin.
        if (
            BetaUser.query.filter_by(email=email, active=True).first() is None
            and not user_obj.admin
        ):
            flash("User is not in the Beta User Group and not allowed to sign in", "danger")
            return False

    if password is not None:
        check = check_password_hash(user_obj.password, password)

        if not check:
            logger.error("SIGNIN: Bad Password")
            return False

    login_user(
        user_obj, remember=remember_me, duration=current_app.config["PERMANENT_SESSION_LIFETIME"]
    )

    session_id = flask_session["_id"]

    update_dict = {"authenticated": True, "active": True, "session_id": session_id}

    try:
        user_qry.update(update_dict)
        DATABASE.session.commit()
        is_successful = True
    except Exception as error:
        is_successful = False
        logger.error(error)

    return is_successful


def _handle_sign_up(
    email: str, password: str = None, origin_host: str = None, oauth_signup: bool = False
):
    # If beta mode is enabled, restrict signup form.
    beta_mode_enable = SettingsSql.query.filter_by(name="APP_ENABLE_BETA").first()

    if beta_mode_enable.value == "True" or beta_mode_enable.value == "true":
        # Only allowed and active beta users.
        if BetaUser.query.filter_by(email=email, active=True).first():
            if _user_exists(email):
                flash("Email already exists!", "danger")
                return False
            new_user = _create_new_user(email, password, oauth_signup)
        else:
            flash("User is not in the Beta User Group and not allowed to sign up", "danger")
            return False
    else:
        if _user_exists(email):
            flash("Email already exists!", "danger")
            return False
        new_user = _create_new_user(email, password, oauth_signup)

    login_user(new_user, duration=current_app.config["PERMANENT_SESSION_LIFETIME"])

    # Update user session id.
    session_id = flask_session["_id"]
    update_dict = {"authenticated": True, "active": True, "session_id": session_id}
    user_qry = UserSql.query.filter_by(email=email)
    user_qry.update(update_dict)
    DATABASE.session.commit()

    # User is signing up without oauth/google in this case.
    if origin_host is not None:
        try:
            # If emails are disabled, return true at this point
            # However, since emails are disabled, email verification does not work upstream.
            # Mark user verified regardless.
            if not current_app.config["APP_ENABLE_EMAIL"]:
                logger.info(
                    "Application emails are disabled - Marking this user verified by default."
                )
                new_user_qry = UserSql.query.filter_by(email=email)
                new_user_qry.update({"verified": True})
                DATABASE.session.commit()
                return True

            # Get a new token
            now = datetime.now(timezone.utc)
            payload = {"exp": now + timedelta(days=1), "iat": now, "sub": str(new_user.user_id)}
            token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

            # Sender, Subject, recipient, html
            if isinstance(token, str):
                verify_link = f"http://{origin_host}/verify?token={token}"
            else:
                verify_link = f"http://{origin_host}/verify?token={token.decode()}"

            # Send welcome email with verification link
            subject = "Welcome to Agents of the System!"
            msg = render_template(
                "email/welcome.html",
                verify_link=verify_link,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
                app_site=origin_host,
            )
        except OperationalError as error:
            logger.error("SIGNUP: Unable to communicate with Celery Backend.")
            logger.error(error)
    else:
        # Send welcome email without verification link
        subject = "Welcome to Agents of the System!"
        msg = render_template(
            "email/welcome.html",
            verify_link=None,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )

    send_email.apply_async(
        [current_app.config["DEFAULT_MAIL_SENDER"], subject, [new_user.email], msg],
        countdown=constants.DEFAULT_EMAIL_DELAY_SECONDS,
    )

    return True


def signin_with_google(email):
    # Check if the user exists.
    user_obj = UserSql.query.filter_by(email=email).first()

    if user_obj:
        return _handle_sign_in(email, None, remember_me=False)
    else:
        logger.debug("Signin with Google: User does not exists.")
        return _handle_sign_up(email, None, None, oauth_signup=True)


def signin(request):
    data = request.form

    # Login Manager - Remember User
    lm_remember = False
    if "remember" in data.keys():
        lm_remember = True

    try:
        email = data["email"]
        password = data["password"]

    except KeyError:
        logger.error("SIGNIN: Missing Data")
        return False

    return _handle_sign_in(email, password, lm_remember)


def signup(request):
    data = request.form

    try:
        password = data["password"]
        email = data["email"]

    except KeyError:
        logger.error("SIGNUP: Missing Data")
        flash("Missing form data. Try Again...", "danger")
        return False

    if not toolbox.is_valid_email(email):
        logger.error("SIGNUP: Invalid Email")
        flash("Invalid Email Address Format. Try Again...", "danger")
        return False

    return _handle_sign_up(email, password, request.host)


def signout(user):
    # The Anonymous User object does not have a user_id attribute if the session times out.
    if hasattr(user, "user_id"):
        user_qry = UserSql.query.filter_by(user_id=user.user_id)
        update_dict = {"active": False, "authenticated": False, "session_id": None}
        user_qry.update(update_dict)
        DATABASE.session.commit()

    logout_user()


def update_profile_password(request):
    data = request.form

    try:
        email = data["hidden_email"]
        current_password = data["current_password"]
        new_password = data["new_password"]
        repeat_password = data["repeat_password"]
    except KeyError as error:
        logger.error("UPDATE_PROFILE: Missing form data!")
        logger.error(error)
        return False

    user_qry = UserSql.query.filter_by(email=email)
    user_obj = user_qry.first()

    if user_obj is None:
        logger.error("UPDATE_PROFILE: User does not exist? This should not happen")
        return

    # Only update the password if the user_obj password string isn't empty.
    if user_obj.password == "":
        logger.warning("User signed up with Google, so cannot change password.")
        flash("You have signed up with Google, so cannot change password.", "warning")
        return False
    # Only update the password if the user entered something into those fields.
    elif current_password != "":
        logger.error("UPDATE_PROFILE: Changing Password.")

        check = check_password_hash(user_obj.password, current_password)

        if not check:
            logger.error("UPDATE_PROFILE: Wrong current password.")
            flash("The current password entered is incorrect.", "danger")
            return False

        # Make sure the passwords match
        if new_password != repeat_password:
            logger.error("UPDATE_PROFILE: Passwords did not match! Try Again.")
            return False

        user_qry.update({"password": generate_password_hash(new_password)})

        flash("Password changed successfully!", "info")

        DATABASE.session.commit()

    return True


def update_profile(request):
    data = request.form

    try:
        username = data["username"]
        email = data["hidden_email"]
        verified = data["verified"]

    except KeyError as error:
        logger.error("UPDATE_PROFILE: Missing form data!")
        logger.error(error)
        return False

    user_qry = UserSql.query.filter_by(email=email)
    user_obj = user_qry.first()

    if user_obj is None:
        logger.error("UPDATE_PROFILE: User does not exist? This should not happen")
        return False

    # Not allowed to update email.
    user_qry.update({"username": username})

    DATABASE.session.commit()

    # Send the verification email if user hits the resend button.
    if verified == "False" and current_app.config["APP_ENABLE_EMAIL"]:
        now = datetime.now(timezone.utc)

        payload = {
            "exp": now + timedelta(days=1),
            "iat": now,
            "sub": str(user_obj.user_id),
        }

        token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

        subject = f"{current_app.config['APP_PRETTY_NAME']} - Verify Email."
        origin_host = request.host

        if isinstance(token, str):
            verify_link = f"http://{origin_host}/verify?token={token}"
        else:
            verify_link = f"http://{origin_host}/verify?token={token.decode()}"

        msg = render_template(
            "email/verify.html",
            verify_link=verify_link,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )

        send_email.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, [user_obj.email], msg]
        )

    return True


def forgot_password(request):
    # Get user email from data.
    data = request.form

    if data is None:
        logger.error("FORGOT: No form data.")
        return False

    if "email" not in data.keys():
        logger.error("FORGOT: Email not in form data.")
        return False

    user_obj = UserSql.query.filter_by(email=data["email"]).first()

    if user_obj is None:
        return False

    if user_obj.password == "":
        logger.error("User signed up with Google, so cannot reset password.")
        flash("You have signed up with Google, so cannot reset password.", "warning")
        return False

    # This token gets a short lifespan
    payload = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
        "sub": str(user_obj.user_id),
    }

    token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

    subject = f"{current_app.config['APP_PRETTY_NAME']} - Forgot Password."
    origin_host = request.host
    reset_link = f"http://{origin_host}/reset?token={token}"

    # Sender, Subject, recipient, html
    try:
        msg = render_template(
            "email/forgot_password.html",
            reset_link=reset_link,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )

        send_email.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, [user_obj.email], msg]
        )
    except OperationalError as error:
        logger.error("ERROR: Unable to communicate with Celery Backend.")
        logger.error(error)

    return True


def reset_password(request):
    data = request.form

    if data is None:
        logger.error("RESET: No form data.")
        return False

    try:
        bearer = data["token"]
    except KeyError:
        logger.error("RESET: No token in the data????")
        return False

    # Make sure the passwords match
    if data["password"] != data["password2"]:
        logger.error("RESET: Passwords did not match!")
        flash("Password did not match. Try again!", "danger")
        return False

    # Attempt to decode.
    try:
        decoded_data = jwt.decode(
            bearer, current_app.config.get("SECRET_KEY"), algorithms=["HS256"]
        )
    except Exception:
        logger.error("RESET: Token invalid... user is not valid.")
        return False

    user_id = decoded_data["sub"]  # Has the user id.

    user_qry = UserSql.query.filter_by(user_id=user_id)
    user_obj = user_qry.first()

    if user_obj is None:
        logger.error("RESET: Token was valid, but the user does not exist?.")
        return False

    # Save the new password
    user_qry.update({"password": generate_password_hash(data["password"])})
    DATABASE.session.commit()

    return True


def verify_email(token):
    # Attempt to decode.
    try:
        decoded_data = jwt.decode(token, current_app.config.get("SECRET_KEY"), algorithms=["HS256"])
    except Exception as error:
        logger.error("VERIFY EMAIL: Token invalid... user is not valid.")
        logger.debug(error)
        return False

    user_id = decoded_data["sub"]  # Has the user id.

    # There are two conditions. The user might already be logged in and trying to verify their
    # email. In this case, check the user_id against the current user to see if they are the
    # same.  This prevents the token from being used by another user that is logged in.
    if hasattr(current_user, "user_id"):
        if int(current_user.user_id) != int(user_id):
            logger.error("VERIFY EMAIL: User ID does not match the current user.")
            return False

    user_qry = UserSql.query.filter_by(user_id=user_id)
    user_obj = user_qry.first()

    if user_obj is None:
        logger.error("RESET: Token was valid, but the user does not exist?.")
        return False

    # Save the new password
    user_qry.update({"verified": True})
    DATABASE.session.commit()

    return True


def get_user_by_id(user_id: int) -> UserSql:
    user_obj = UserSql.query.filter_by(user_id=user_id).first()

    if user_obj is None:
        logger.error("Error: User does not exist!")
        return None

    return user_obj


def delete_subscription(user_id: int) -> None:
    """
    For each agent:
    1. Turn off each monitor.
    2. Stop any potential monitor task(s).
    3. Detach agent shares to groups and/or friends.
    """
    skip_first_agent = True
    user_agents = agent_control.get_agents_by_owner(user_id)

    for agent in user_agents:
        # Agent Monitors.
        agent_obj = agent_control.get_agent_by_id(agent["agent_id"], as_obj=True)
        agent_monitors = agent_obj.attached_monitors.all()

        for monitor in agent_monitors:
            # Set monitor to inactive, revoke task, and delete faults.
            monitor.active = False

            task_id = monitor.task_id
            monitor.task_id = None

            if task_id is not None:
                CELERY.control.revoke(task_id, terminate=True)

            for fault in monitor.monitor_faults.all():
                DATABASE.session.delete(fault)
            DATABASE.session.commit()

        # Agent Shares.
        group_shares = agent_obj.groups_with_access.all()
        friend_shares = agent_obj.friends_with_access.all()
        for group in group_shares:
            DATABASE.session.delete(group)

        for friend in friend_shares:
            DATABASE.session.delete(friend)

        if skip_first_agent:
            skip_first_agent = False
            continue
        else:
            agent_obj.active = False

    DATABASE.session.commit()
