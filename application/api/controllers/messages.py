import traceback

from flask_login import current_user
from datetime import datetime

from application.common import logger
from application.extensions import DATABASE
from application.models.message import Messages


def create_global_message(message, subject) -> None:
    new_message = Messages()

    new_message.message = message
    new_message.subject = subject

    new_message.sender_id = 1
    new_message.is_global = True
    new_message.timestamp = datetime.now()

    try:
        DATABASE.session.add(new_message)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical("Unable to create global message")
        logger.critical(error)
        traceback.print_exc()
        DATABASE.session.rollback()


def create_direct_message(sender_id, recipient_id, message, subject) -> None:
    new_message = Messages()

    new_message.message = message
    new_message.subject = subject

    new_message.sender_id = sender_id
    new_message.recipient_id = recipient_id
    new_message.is_global = False
    new_message.timestamp = datetime.now()

    try:
        DATABASE.session.add(new_message)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical("Unable to create direct message")
        logger.critical(error)
        traceback.print_exc()
        DATABASE.session.rollback()


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
