import json
import stripe

from datetime import datetime, timezone
from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
    flash,
    current_app,
    jsonify,
)
from flask_login import current_user

from application.api.controllers import users as user_control
from application.api.public.forms import (
    SignupForm,
    SignInForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)
from application.common import logger
from application.common.toolbox import _get_setting
from application.extensions import CSRF, DATABASE
from application.models.user import UserSql
from application.models.setting import SettingsSql
from application.workers.email import send_email

public = Blueprint("public", __name__)


# Health Routes
@public.route("/health")
def health():
    return jsonify("Alive")


# Public Routes
@public.route("/")
def index():
    return render_template("public/index.html", pretty_name=current_app.config["APP_PRETTY_NAME"])


@public.route("/about")
def about():
    return render_template("public/about.html", pretty_name=current_app.config["APP_PRETTY_NAME"])


@public.route("/coming/soon")
def coming_soon():
    return render_template(
        "public/comingsoon.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


@public.route("/pricing")
def pricing():
    return render_template(
        "public/pricing.html", pretty_name=current_app.config["APP_PRETTY_NAME"], is_internal=False
    )


@public.route("/support")
def support():
    return render_template("public/support.html", pretty_name=current_app.config["APP_PRETTY_NAME"])


# TODO - Add privacy policy page
@public.route("/privacy/policy")
def privacy_policy():
    return render_template(
        "public/privacy-policy.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


# TODO - Add T&C page
@public.route("/terms")
def terms_and_conditions():
    return render_template(
        "public/terms-and-conditions.html",
        pretty_name=current_app.config["APP_PRETTY_NAME"],
    )


@public.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()

    # If already signed in, got to main app page.
    if current_user.is_authenticated:
        return redirect(url_for("protected.dashboard"))

    if request.method == "POST":
        result = user_control.signup(request)
        if result:
            # TODO - Maybe go to an onboarding page.
            return redirect(url_for("protected.dashboard"))
        else:
            return render_template(
                "public/signup.html",
                form=form,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
            )
    else:
        return render_template(
            "public/signup.html",
            form=form,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
        )


@public.route("/signin", methods=["GET", "POST"])
def signin():
    form = SignInForm()

    # If already signed in, got to main app page.
    if current_user.is_authenticated:
        return redirect(url_for("protected.dashboard"))

    if request.method == "POST":
        result = user_control.signin(request)
        if result:
            return redirect(url_for("protected.dashboard"))
        else:
            flash("Incorrect Username or Password!", "danger")
            return render_template(
                "public/signin.html",
                form=form,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
                email_enabled=current_app.config["APP_ENABLE_EMAIL"],
            )
    else:
        return render_template(
            "public/signin.html",
            form=form,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            email_enabled=current_app.config["APP_ENABLE_EMAIL"],
        )


@public.route("/signout")
def signout():
    user_control.signout(current_user)
    return redirect(url_for("public.index"))


@public.route("/forgot", methods=["GET", "POST"])
def forgot():
    form = ForgotPasswordForm()

    # If already signed in, got to main app page.
    if current_user.is_authenticated:
        return redirect(url_for("protected.dashboard"))

    if request.method == "POST":
        result = user_control.forgot_password(request)
        if result:
            flash("Please check your email.", "info")
            return render_template(
                "public/forgot.html",
                form=form,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
            )
        else:
            flash("User does not exist!", "danger")
            return render_template(
                "public/forgot.html",
                form=form,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
            )
    else:
        return render_template(
            "public/forgot.html",
            form=form,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
        )


@public.route("/reset", methods=["GET", "POST"])
def reset():
    form = ResetPasswordForm()

    token = request.args.get("token", None, type=str)

    # In this case, the reset has been POSTed and there ought to be
    # a reset token.
    if request.method == "POST":
        result = user_control.reset_password(request)

        if result:
            flash("Password reset successful! Please login.", "info")
            return redirect(url_for("public.signin"))
        else:
            # User password didn't match or password strength too low.
            token = request.form["token"]
            return render_template(
                "public/reset.html",
                form=form,
                reset_token=token,
                fix_url=True,
                pretty_name=current_app.config["APP_PRETTY_NAME"],
            )

    # In this case, the user clicked the link from the email.
    elif request.method == "GET" and token is not None:
        return render_template(
            "public/reset.html",
            form=form,
            reset_token=token,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
        )

    # In this case, someone navigated here and we shouldn't show them the
    # form.
    else:
        # If already signed in, got to main app page.
        if current_user.is_authenticated:
            return redirect(url_for("protected.dashboard"))

        return redirect(url_for("public.index"))


@public.route("/verify", methods=["GET"])
def verify():
    token = request.args.get("token", None, type=str)

    # The user is not logged in.
    if current_user.is_active is False:
        # Login the user and verify the email address.
        result = user_control.verify_email(token)
        if result:
            flash("Email verified! Please log in.", "info")
            return redirect(url_for("public.signin"))
        else:
            flash(
                "Email not verified! Please resend the verification email and try again.",
                "danger",
            )
            return redirect(url_for("public.index"))
    # The user was logged in, verify, then take to account
    # page.
    else:
        result = user_control.verify_email(token)

        if result:
            flash("Email verified. Thank you!", "info")
            return redirect(url_for("protected.account"))
        else:
            flash(
                "Email not verified! Please resend the verification email and try again.",
                "danger",
            )
            return redirect(url_for("protected.dashboard"))


@public.route("/webhook", methods=["POST"])
@CSRF.exempt
def webhook():
    try:
        request_data = json.loads(request.data)
    except json.decoder.JSONDecodeError as error:
        logger.critical(error)
        request_data = request.data

    # Sender, Subject, recipient, html
    origin_host = request.host
    email_subject = None
    email_message = None
    customer_email = None

    setting_objs = SettingsSql.query.all()
    webhook_secret = _get_setting("STRIPE_WEBHOOK_SECRET", setting_objs)
    email_enabled_str = _get_setting("APP_ENABLE_EMAIL", setting_objs)
    email_enabled = True if email_enabled_str.lower() == "true" else False

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and
        # secret if webhook signing is configured.
        signature = request.headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret
            )
            data = event["data"]
        except Exception as e:
            logger.critical("THERE WAS AN EXCEPTION: ")
            logger.critical(e)
            return e, 500
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event["type"]
    else:
        data = request_data["data"]
        event_type = request_data["type"]

    data_object = data["object"]

    logger.info("Event is: " + event_type)

    if event_type == "checkout.session.completed":
        logger.debug("🔔 Payment succeeded!")

        # Use this to query database
        customer_email = data_object["customer_email"]

        # Use this to cancel the subscription.
        subscription = data_object["subscription"]

        # Use this for future reference.
        customer = data_object["customer"]

        # If the customer is re-subscribing, then stripe is going to pass the customer id instead
        # of the email.
        if customer_email is None:
            usr_qry = UserSql.query.filter_by(customer_id=customer)
            customer_email = usr_qry.first().email
        else:
            usr_qry = UserSql.query.filter_by(email=customer_email)

        update_dict = {
            "subscribed": True,
            "subscription_id": subscription,
            "customer_id": customer,
        }

        now = datetime.now(timezone.utc)

        email_subject = "Subscription Confirmation"
        email_message = render_template(
            "email/new_subscriber.html",
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=origin_host,
            renewal_day=now.day,
        )

        usr_qry.update(update_dict)
        DATABASE.session.commit()

    elif event_type == "customer.subscription.updated":
        logger.debug("🔔 Subscription updated!")
        logger.debug(data_object)
        customer_id = data_object["customer"]
        cancel_at = data_object["cancel_at"]

        usr_qry = UserSql.query.filter_by(customer_id=customer_id)
        user_obj = usr_qry.first()

        if user_obj:
            customer_email = user_obj.email

        # Update in this case the user is cancelling.
        if cancel_at is not None:
            email_subject = "Sorry to see you go!"
            email_message = render_template(
                "email/cancel_subscriber.html",
                pretty_name=current_app.config["APP_PRETTY_NAME"],
                app_site=origin_host,
            )
        else:
            # Else, the user is renewing, returning, etc..
            email_subject = "Subscription Renewed"
            email_message = render_template(
                "email/new_subscriber.html",
                pretty_name=current_app.config["APP_PRETTY_NAME"],
                app_site=origin_host,
            )

    elif event_type == "customer.subscription.deleted":
        logger.debug("🔔 Customer canceled their subscription!")

        customer_id = data_object["customer"]

        usr_qry = UserSql.query.filter_by(customer_id=customer_id)
        user_obj = usr_qry.first()

        if user_obj:
            customer_email = user_obj.email
            usr_qry.update({"subscribed": False, "subscription_id": ""})
            DATABASE.session.commit()
            user_control.delete_subscription(user_obj.user_id)

        email_subject = "Your subscription has ended."
        email_message = render_template(
            "email/end_subscriber.html",
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=origin_host,
        )

    else:
        logger.debug(f"Received Event: {event_type} but not doing anything with it.")

    # If all of these items were populated, then send the email.
    if email_enabled and email_subject and email_message and customer_email:
        send_email.apply_async(
            [
                current_app.config["DEFAULT_ADMIN_EMAIL"],
                email_subject,
                [customer_email],
                email_message,
            ]
        )

    return jsonify({"status": "success"})
