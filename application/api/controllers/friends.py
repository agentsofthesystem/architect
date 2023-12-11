import uuid

from application.common import logger
from application.extensions import DATABASE
from application.models.user import UserSql


def generate_friend_code(email: str):
    return uuid.uuid5(uuid.NAMESPACE_DNS, email)


def add_friend_code_to_user(user_id: int, friend_code: str):
    user_qry = UserSql.query.filter_by(user_id=user_id)
    update_dict = {"friend_code": friend_code}

    try:
        user_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    return True
