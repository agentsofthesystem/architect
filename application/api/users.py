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

from application.extensions import DATABASE
from application.common import logger
from application.common.tools import check_password
from application.models.user import UserSql
from application.api.workers.email import emailer


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

    check = check_password_hash(user_obj.password, password)

    if not check:
        logger.error("SIGNIN: Bad Password")
        return False

    update_dict = {"is_authenticated": True, "active": True}

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
    login_user(user_obj, remember=lm_remember, duration=timedelta(hours=24))

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
        flash("There was an internal error...", "danger")
        return False

    check_user_obj = UserSql.query.filter_by(email=email).first()

    if check_user_obj:
        flash("Email already exists!", "danger")
        return False

    new_user = UserSql()

    new_user.active = True
    new_user.authenticated = True
    new_user.admin = False

    new_user.username = user
    new_user.email = email
    new_user.password = generate_password_hash(password)

    new_user.first_name = first
    new_user.last_name = last

    try:
        DATABASE.session.add(new_user)
        DATABASE.session.commit()
    except Exception as error:
        logger.error(error)

    login_user(new_user)

    now = datetime.utcnow()

    payload = {"exp": now + timedelta(days=1), "iat": now, "sub": str(new_user.user_id)}

    token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

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

        # Sender, Subject, recipient, html

        # Send welcome email
        subject = f"Welcome to {current_app.config['APP_PRETTY_NAME']}!"
        msg = render_template(
            "email/welcome.html",
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )
        emailer.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, new_user.email, msg]
        )

        # Send email verification email.
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
        emailer.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, new_user.email, msg],
            eta=now + timedelta(seconds=60),
        )

    except OperationalError as error:
        logger.error("SIGNUP: Unable to communicate with Celery Backend.")
        logger.error(error)

    return True


def signout(user):
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

        token = jwt.encode(
            payload, current_app.config.get("SECRET_KEY"), algorithm="HS256"
        )

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

        emailer.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, user_obj.email, msg]
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
        "exp": datetime.utcnow()
        + timedelta(minutes=15),  # This token gets a short lifespan
        "iat": datetime.utcnow(),
        "sub": str(user_obj.user_id),
    }

    token = jwt.encode(payload, current_app.config.get("SECRET_KEY"), algorithm="HS256")

    subject = f"{current_app.config['APP_PRETTY_NAME']} - Forgot Password."
    origin_host = request.host
    reset_link = f"http://{origin_host}/reset?token={token}"

    """
    static_path = str(url_for('static', filename='uix/assets/img/logo-white.svg'))
    base_path = str(os.path.dirname(current_app.instance_path))
    full_path = os.path.join(base_path, 'application', static_path[1:])

    attachment={}
    attachment['path'] = full_path
    attachment['title'] = 'email-logo.jpg'
    attachment['type'] = 'image/jpeg'
    attachment['cid'] = "email-logo"
    """

    # Sender, Subject, recipient, html
    try:
        # Add for attachment
        # cid=attachment["cid"]

        msg = render_template(
            "email/forgot_password.html",
            reset_link=reset_link,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )

        # Add for attachment
        # kwargs={'attachment_list': [attachment]}

        emailer.apply_async(
            [current_app.config["DEFAULT_MAIL_SENDER"], subject, user_obj.email, msg]
        )
    except OperationalError as error:
        logger.error("FORGOT: Unable to communicate with Celery Backend.")
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

    # Check for password strength
    if check_password(data["password"]) is False:
        flash("Password must be at least 7 characters.", "danger")
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
        decoded_data = jwt.decode(
            token, current_app.config.get("SECRET_KEY"), algorithms=["HS256"]
        )
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
