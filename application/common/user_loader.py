from application.common import logger
from application.extensions import LOGIN_MANAGER
from application.models.user import UserSql


@LOGIN_MANAGER.user_loader
def load_user(user_id):
    logger.debug(f"USER_LOADER: User ID for session: {user_id}")

    user_obj = None

    # Only load user if it exists.
    if user_id != "None":
        # Get user and return
        user_qry = UserSql.query.filter_by(user_id=user_id)
        user_obj = user_qry.first()

        if user_obj is None:
            return user_obj

    return user_obj
