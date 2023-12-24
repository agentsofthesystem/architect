from flask import flash, redirect, url_for
from flask import session as flask_session
from flask_login import logout_user

from application.common import logger
from application.extensions import LOGIN_MANAGER
from application.models.user import UserSql


@LOGIN_MANAGER.user_loader
def load_user(user_id):
    logger.debug(f"USER_LOADER: User ID for session: {user_id}")

    user_obj = None
    browser_session_id = None

    if "session_id" in flask_session:
        browser_session_id = str(flask_session["session_id"])

    # Only load user if it exists.
    if user_id != "None":
        # Get user and return
        user_qry = UserSql.query.filter_by(user_id=user_id)
        user_obj = user_qry.first()

        if user_obj is None:
            return user_obj

        if browser_session_id:
            if browser_session_id != user_obj.session_id:
                return None

            logger.info("*****************************")
            logger.info(browser_session_id)
            logger.info(user_obj.session_id)
            logger.info("*****************************")

    return user_obj
