import jwt

from datetime import datetime, timedelta
from flask import (
    current_app,
    render_template,
    flash,
    session,
)
from flask_login import login_user, logout_user
from kombu.exceptions import OperationalError
from werkzeug.security import generate_password_hash, check_password_hash

from application.api.controllers.friends import generate_friend_code
from application.common import logger, constants
from application.extensions import DATABASE
from application.models.beta_user import BetaUser
from application.models.setting import SettingsSql
from application.models.user import UserSql
from application.workers.email import send_email


def _create_new_user(user, email, password, first, last):
    new_user = UserSql()

    new_user.active = True
    new_user.authenticated = True
    new_user.admin = False

    new_user.username = user
    new_user.email = email
    new_user.password = generate_password_hash(password)
    new_user.friend_code = generate_friend_code(email)

    new_user.first_name = first
    new_user.last_name = last

    try:
        DATABASE.session.add(new_user)
        DATABASE.session.commit()
    except Exception as error:
        logger.error(error)

    return new_user


def _user_exists(email):
    check_user_obj = UserSql.query.filter_by(email=email).first()

    return False if check_user_obj is None else True


def signin(request):
    data = request.form

    try:
        email = data["email"]
        password = data["password"]

    except KeyError:
        logger.error("SIGNIN: Missing Data")
        return False

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

    check = check_password_hash(user_obj.password, password)

    if not check:
        logger.error("SIGNIN: Bad Password")
        return False

    update_dict = {"authenticated": True, "active": True}

    try:
        user_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.error(error)

    # Login Manager - Remember User
    lm_remember = False
    if "remember" in data.keys():
        lm_remember = True

    logger.info(f"SIGNIN: Remember User: {lm_remember}")

    session.permanent = True

    login_user(
        user_obj, remember=lm_remember, duration=current_app.config["PERMANENT_SESSION_LIFETIME"]
    )

    return True


def signup(request):
    data = request.form

    try:
        user = data["username"]
        password = data["password"]
        email = data["email"]
        first = data["first"]
        last = data["last"]

    except KeyError:
        logger.error("SIGNUP: Missing Data")
        flash("Missing form data. Try Again...", "danger")
        return False

    if user == email:
        flash("Your username should not also be your email address. Try Again!", "warning")
        return False

    # If beta mode is enabled, restrict signup form.
    beta_mode_enable = SettingsSql.query.filter_by(name="APP_ENABLE_BETA").first()

    if beta_mode_enable.value == "True" or beta_mode_enable.value == "true":
        # Only allowed and active beta users.
        if BetaUser.query.filter_by(email=email, active=True).first():
            if _user_exists(email):
                flash("Email already exists!", "danger")
                return False
            new_user = _create_new_user(user, email, password, first, last)
        else:
            flash("User is not in the Beta User Group and not allowed to sign up", "danger")
            return False
    else:
        if _user_exists(email):
            flash("Email already exists!", "danger")
            return False
        new_user = _create_new_user(user, email, password, first, last)

    login_user(new_user)

    now = datetime.utcnow()

    payload = {"exp": now + timedelta(days=1), "iat": now, "sub": str(new_user.user_id)}

    token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

    try:
        # If emails are disabled, return true at this point
        # However, since emails are disabled, email verification does not work upstream.
        # Mark user verified regardless.
        if not current_app.config["APP_ENABLE_EMAIL"]:
            logger.info("Application emails are disabled - Marking this user verified by default.")
            new_user_qry = UserSql.query.filter_by(email=email)
            new_user_qry.update({"verified": True})
            DATABASE.session.commit()
            return True

        # Sender, Subject, recipient, html
        origin_host = request.host

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
        send_email.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, [new_user.email], msg],
            countdown=constants.DEFAULT_EMAIL_DELAY_SECONDS,
        )

    except OperationalError as error:
        logger.error("SIGNUP: Unable to communicate with Celery Backend.")
        logger.error(error)

    return True


def signout(user):
    user_qry = UserSql.query.filter_by(user_id=user.user_id)
    update_dict = {"active": False, "authenticated": False}
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

    # Only update the password if the user entered something into those fields.
    if current_password != "":
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
        first = data["first"]
        last = data["last"]
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
    user_qry.update({"username": username, "first_name": first, "last_name": last})

    DATABASE.session.commit()

    # Send the verification email if user hits the resend button.
    if verified == "False" and current_app.config["APP_ENABLE_EMAIL"]:
        now = datetime.utcnow()

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

    payload = {
        "exp": datetime.utcnow() + timedelta(minutes=15),  # This token gets a short lifespan
        "iat": datetime.utcnow(),
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
