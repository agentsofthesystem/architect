import stripe

from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    current_app,
    redirect,
    url_for,
)
from flask_login import login_required, current_user

from application.api import users, messages
from application.common import logger
from application.common.tools import (
    verified_required,
    admin_required,
    _get_setting,
)
from application.extensions import DATABASE
from application.models.user import UserSql
from application.models.setting import SettingsSql
from application.uix.protected.forms import (
    AccountProfileForm,
    AccountUpdatePasswordForm,
    GlobalMessageForm,
    DirectMessageForm,
)

protected = Blueprint("protected", __name__, url_prefix="/app")


@protected.route("/main")
@login_required
def main():
    return render_template(
        "uix/app.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


@protected.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "uix/dashboard.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


@protected.route("/system/agents")
@login_required
@verified_required
def system_agents():
    return render_template(
        "uix/system_agents.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


@protected.route("/system/crews")
@login_required
@verified_required
def system_crews():
    return render_template(
        "uix/system_crews.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


@protected.route("/system/friends")
@login_required
@verified_required
def system_friends():
    return render_template(
        "uix/system_friends.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
    )


# @protected.route("/example/verified/page")
# @login_required
# @verified_required
# def example_verified_page():
#     return render_template(
#         "uix/example_verified_page.html",
#         pretty_name=current_app.config["APP_PRETTY_NAME"],
#     )


# @protected.route("/example/paid/page")
# @login_required
# @verified_required
# @subscription_required
# def example_paid_page():
#     return render_template(
#         "uix/example_paid_page.html", pretty_name=current_app.config["APP_PRETTY_NAME"]
#     )


@protected.route("/success")
def success():
    return redirect(url_for("protected.account", tab="billing"))


@protected.route("/account/update/password", methods=["GET", "POST"])
@login_required
def update_account_password():
    if request.method == "POST":
        if not users.update_profile_password(request):
            flash("Password did not match!", "danger")

    return redirect(url_for("protected.account"))


@protected.route("/account", methods=["GET", "POST"])
@login_required
def account():
    profile_form = AccountProfileForm()
    update_password_form = AccountUpdatePasswordForm()

    verified = "True" if current_user.verified else "False"

    active_tab = request.args.get("tab", "account", type=str)

    if request.method == "POST":
        if not users.update_profile(request):
            # Redirect back to GET of this same endpoint. This
            # ensures user loader updates current_user object.
            flash("Unable to update profile!", "danger")

            return redirect(url_for("protected.account"))

    else:
        return render_template(
            "uix/account.html",
            profile_form=profile_form,
            update_password_form=update_password_form,
            verified=verified,
            active_tab=active_tab,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            payments_enabled=current_app.config["APP_ENABLE_PAYMENTS"],
            email_enabled=current_app.config["APP_ENABLE_EMAIL"],
        )

    return redirect(url_for("protected.account"))


@protected.route("/create-checkout-session", methods=["POST", "GET"])
@login_required
def create_checkout_session():
    price_type = request.args.get("price_type", "NONE", str)

    if price_type == "MONTHLY":
        settings_obj = SettingsSql.query.filter_by(
            name="STRIPE_MONTHLY_PRICE_ID"
        ).first()
        price_id = settings_obj.value
    elif price_type == "ANNUAL":
        settings_obj = SettingsSql.query.filter_by(
            name="STRIPE_ANNUAL_PRICE_ID"
        ).first()
        price_id = settings_obj.value
    else:
        logger.critical("Error: Incorrect price type supplied for check out session.")
        return "", 400

    setting_objs = SettingsSql.query.filter_by(category="payments").all()
    stripe_secret_key = _get_setting("STRIPE_SECRET_KEY", setting_objs)

    stripe.api_key = stripe_secret_key

    http_mode = "http" if current_app.config["ENV"] == "development" else "https"

    success_url = (
        f"{http_mode}://{request.host}/app/success"
        + "?session_id={CHECKOUT_SESSION_ID}"
    )
    cancel_url = f"{http_mode}://{request.host}/app/account?tab=billing"

    logger.info(f"Success URL: {success_url}")
    logger.info(f"Cancel URL: {cancel_url}")

    line_items = [
        {
            "price": price_id,
            "quantity": 1,
        },
    ]

    try:
        if current_user.customer_id:
            # Existing / Returning Customer
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                customer=current_user.customer_id,
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                allow_promotion_codes=True,
                customer_update={"address": "auto"},
                payment_method_collection="if_required",
            )
        else:
            # New customer
            checkout_session = stripe.checkout.Session.create(
                line_items=line_items,
                customer_email=current_user.email,
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                allow_promotion_codes=True,
                payment_method_collection="if_required",
            )
    except Exception as error:
        logger.critical(error)
        return str(error), 500

    return redirect(checkout_session.url, code=303)


@protected.route("/customer_portal", methods=["GET", "POST"])
@login_required
def customer_portal():
    # Set secret key

    setting_objs = SettingsSql.query.filter_by(category="payments").all()
    stripe_secret_key = _get_setting("STRIPE_SECRET_KEY", setting_objs)
    # monthly_price_id =  _get_setting("STRIPE_MONTHLY_PRICE_ID", setting_objs)
    # annual_price_id =  _get_setting("STRIPE_ANNUAL_PRICE_ID", setting_objs)

    stripe.api_key = stripe_secret_key

    privacy_policy_url = url_for("public.privacy_policy", _external=True).replace(
        "http", "https"
    )
    terms_url = url_for("public.terms_and_conditions", _external=True).replace(
        "http", "https"
    )

    # Build customer portal.
    # Reference API:
    # https://stripe.com/docs/api/customer_portal/configurations/create?lang=python#create_portal_configuration-features
    portal_config = stripe.billing_portal.Configuration.create(
        features={
            "customer_update": {
                "enabled": True,
                "allowed_updates": ["address", "phone"],
            },
            "subscription_cancel": {"enabled": True, "mode": "at_period_end"},
            # "subscription_update":{
            #     "enabled": True,
            #     "default_allowed_updates": ["price"]
            # },
            "invoice_history": {"enabled": True},
            "payment_method_update": {"enabled": True},
        },
        business_profile={
            "headline": "Thank you for being a customer!",
            "privacy_policy_url": privacy_policy_url,
            "terms_of_service_url": terms_url,
        },
    )

    response = stripe.billing_portal.Session.create(
        customer=current_user.customer_id,
        return_url=f"http://{request.host}/app/account?tab=billing",
        configuration=portal_config,
    )

    # Get the portal url
    portal_url = response["url"]

    # Redirect to the portal
    return redirect(portal_url)


@protected.route("/admin/submit/global", methods=["POST"])
@admin_required
def admin_submit_global_message():
    global_message = GlobalMessageForm()

    if request.method == "POST" and global_message.validate_on_submit():
        messages.create_global_message(
            global_message.message.data, global_message.subject.data
        )
        global_message.message.data = ""
        global_message.subject.data = ""

    return redirect(url_for("protected.admin"))


@protected.route("/admin/submit/direct", methods=["POST"])
@admin_required
def admin_submit_direct_message():
    message = DirectMessageForm()

    if request.method == "POST" and message.validate_on_submit():
        logger.info("Evaluating DIRECT Message POST....")
        messages.create_direct_message(
            1, message.recipient_id.data, message.message.data, message.subject.data
        )
        message.recipient_id.data = ""
        message.subject.data = ""
        message.message.data = ""

    return redirect(url_for("protected.admin"))


@protected.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    global_message = GlobalMessageForm()
    message = DirectMessageForm()

    # All non-admin users
    all_users = UserSql.query.filter_by(admin=False).all()

    return render_template(
        "uix/admin.html",
        global_message=global_message,
        message=message,
        all_users=all_users,
        pretty_name=current_app.config["APP_PRETTY_NAME"],
    )


@protected.route("/messages", methods=["GET", "POST"])
@login_required
def user_messages():
    # Update last message read time for current user.
    if request.method == "POST":
        json_data = request.json
        status = json_data["status"]
        if status == "MARK_READ":
            usr_qry = UserSql.query.filter_by(user_id=current_user.user_id)
            usr_qry.update({"last_message_read_time": datetime.now()})
            DATABASE.session.commit()

    # Messages: Un-read and of type global and direct.
    global_message_list = messages.get_global_messages()
    direct_message_list = messages.get_direct_messages()

    is_global_message = True if len(global_message_list) > 0 else False
    is_direct_message = True if len(direct_message_list) > 0 else False

    for dm in direct_message_list:
        sender_id = dm.sender_id
        user_obj = UserSql.query.filter_by(user_id=sender_id).first()
        setattr(dm, "username", user_obj.username)

    return render_template(
        "uix/messages.html",
        global_message_list=global_message_list,
        direct_message_list=direct_message_list,
        is_global_message=is_global_message,
        is_direct_message=is_direct_message,
        pretty_name=current_app.config["APP_PRETTY_NAME"],
    )
