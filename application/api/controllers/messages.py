import traceback

from datetime import datetime, timezone
from flask import current_app, render_template
from flask_login import current_user
from kombu.exceptions import OperationalError

from application.common import logger
from application.common.constants import MessageCategories
from application.extensions import DATABASE
from application.models.message import Messages
from application.models.user import UserSql
from application.models.setting import SettingsSql
from application.workers.email import send_global_email, send_email


# Determine if the admin has enabled the system for email notifications.
def is_email_enabled() -> bool:
    setting = SettingsSql.query.filter_by(name="APP_ENABLE_EMAIL").first()
    setting_test = setting.value.lower()
    return True if setting_test == "true" else False


def _create_message(
    sender_id: int, recipient_id: int, message: str, subject: str, is_global: bool = False
) -> None:
    # Create message and enter into database.
    new_message = Messages()

    new_message.message = message
    new_message.subject = subject

    new_message.sender_id = sender_id

    # We don't need to set the recipient_id if it's a global message.
    if not is_global:
        new_message.recipient_id = recipient_id

    new_message.is_global = is_global
    new_message.timestamp = datetime.now(timezone.utc)

    try:
        DATABASE.session.add(new_message)
        DATABASE.session.commit()
    except Exception as error:
        message_type = "global" if is_global else "direct"
        logger.critical(f"Unable to create {message_type} message")
        logger.critical(error)
        traceback.print_exc()
        DATABASE.session.rollback()


def _is_user_category_disabled(user_id: int, category: MessageCategories, is_email=False) -> bool:
    is_disabled = False

    user = UserSql.query.filter_by(user_id=user_id).first()
    user_properties = user.properties

    if category == MessageCategories.SOCIAL and not is_email:
        if "NOTIFICATION_DM_SOCIAL_ENABLED" in user_properties:
            is_disabled = True
    elif category == MessageCategories.SOCIAL and is_email:
        if "NOTIFICATION_EMAIL_SOCIAL_ENABLED" in user_properties:
            is_disabled = True
    elif category == MessageCategories.MONITOR and not is_email:
        if "NOTIFICATION_DM_MONITOR_ENABLED" in user_properties:
            is_disabled = True
    elif category == MessageCategories.MONITOR and is_email:
        if "NOTIFICATION_EMAIL_MONITOR_ENABLED" in user_properties:
            is_disabled = True

    return is_disabled


def create_global_message(message, subject) -> None:
    # Enter the message into the database.
    _create_message(-1, None, message, subject, is_global=True)

    if not is_email_enabled():
        logger.warning("Email is disabled. Not sending global email")
        return

    # Send Email to all users.
    try:
        msg = render_template(
            "email/email_notification.html",
            message_content=message,
            pretty_name=current_app.config["APP_PRETTY_NAME"],
            app_site=current_app.config["APP_WEBSITE"],
        )

        send_global_email.apply_async([subject, msg])
    except OperationalError as error:
        logger.error("ERROR: Unable to communicate with Celery Backend.")
        logger.error(error)


def create_direct_message(
    sender_id: int,
    recipient_id: int,
    message: str,
    subject: str,
    category: MessageCategories = MessageCategories.NOT_SET,
) -> None:
    user_obj = UserSql.query.filter_by(user_id=recipient_id).first()

    rendered_message = render_template(
        "email/email_notification.html",
        message_content=message,
        pretty_name=current_app.config["APP_PRETTY_NAME"],
        app_site=current_app.config["APP_WEBSITE"],
    )

    if category == MessageCategories.NOT_SET:
        logger.error("Message category not set.")

    elif category == MessageCategories.ADMIN:
        # The admin category cannot be disabled.
        _create_message(sender_id, recipient_id, message, subject, is_global=False)

        if not is_email_enabled():
            logger.warning("Email is disabled. Not sending ADMIN email")
            return

        try:
            send_email.apply_async(
                [
                    current_app.config["DEFAULT_ADMIN_EMAIL"],
                    subject,
                    [user_obj.email],
                    rendered_message,
                ]
            )
        except OperationalError as error:
            logger.error("ERROR: Unable to communicate with Celery Backend.")
            logger.error(error)

    elif category == MessageCategories.SOCIAL or category == MessageCategories.MONITOR:
        if not _is_user_category_disabled(recipient_id, category):
            _create_message(sender_id, recipient_id, message, subject, is_global=False)

        if not is_email_enabled():
            logger.warning("Email is disabled. Not sending SOCIAL/MONITOR email")
            return

        if not _is_user_category_disabled(recipient_id, category, is_email=True):
            # Send Email to all users.
            try:
                send_email.apply_async(
                    [
                        current_app.config["DEFAULT_MAIL_SENDER"],
                        subject,
                        [user_obj.email],
                        rendered_message,
                    ]
                )
            except OperationalError as error:
                logger.error("ERROR: Unable to communicate with Celery Backend.")
                logger.error(error)


def message_user_list(
    sender_id: int, user_list: list, message: str, subject: str, category: MessageCategories
) -> None:
    for user_id in user_list:
        if MessageCategories.MONITOR == category:
            create_direct_message(sender_id, user_id, message, subject, category)
        else:
            logger.critical("Invalid category for message_user_list")


def get_direct_messages():
    """Return unexpired & global notification types only."""
    last_read_time = current_user.last_message_read_time or datetime(1900, 1, 1)
    return (
        Messages.query.filter_by(recipient=current_user)
        .filter(Messages.timestamp > last_read_time)
        .all()
    )


def get_global_messages():
    """Return unexpired & global notification types only."""
    last_read_time = current_user.last_message_read_time or datetime(1900, 1, 1)
    return (
        Messages.query.filter_by(is_global=True).filter(Messages.timestamp > last_read_time).all()
    )
