from datetime import datetime, timezone
from flask_login import current_user

from application.common import timezones, logger, constants
from application.extensions import DATABASE
from application.models.agent import Agents
from application.models.agent_log import AgentLog
from application.models.user import UserSql


# A function to create a new log entry using user_id and agent_id
def create_agent_log(user_id: int, agent_id: int, message: str, is_automated: bool = False) -> bool:
    user_obj = UserSql.query.filter_by(user_id=user_id).first()

    if user_obj is None:
        logger.error(f"User ID {user_id} does not exist!")
        return False

    agent_obj = Agents.query.filter_by(agent_id=agent_id).first()

    if agent_obj is None:
        logger.error(f"Agent ID {agent_id} does not exist!")
        return False

    new_log = AgentLog(
        agent_id=agent_id,
        user_id=user_id,
        message=message,
        timestamp=datetime.now(timezone.utc),
        is_automated=is_automated,
    )

    try:
        DATABASE.session.add(new_log)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error creating agent log: {e}")
        DATABASE.session.rollback()
        return False

    return True


# A function to get the 3 most recent agent logs
def get_recent_agent_logs(agent_id: int) -> list[dict]:
    # User properties to determine whether or not to apply offset
    user_properties = current_user.properties
    format_str = timezones._apply_time_log_format_preference(user_properties)

    if "USER_TIMEZONE" in user_properties:
        user_timezone = user_properties["USER_TIMEZONE"]
        user_timezone = timezones.tz_label_to_timezone(user_timezone)
    else:
        user_timezone = timezones.tz_label_to_timezone(constants.DEFAULT_USER_TIMEZONE)

    # Get the 5 most recent agent logs
    recent_agent_logs = (
        AgentLog.query.filter_by(agent_id=agent_id)
        .order_by(AgentLog.timestamp.desc())
        .limit(constants.DEFAULT_AGENT_LOGS_PER_AGENT_FREE)
        .all()
    )
    return [log.to_dict(format_str, user_timezone) for log in recent_agent_logs]


# A function to get all agent logs
def get_all_agent_logs(agent_id: int) -> list[dict]:
    # User properties to determine whether or not to apply offset
    user_properties = current_user.properties
    format_str = timezones._apply_time_log_format_preference(user_properties)

    if "USER_TIMEZONE" in user_properties:
        user_timezone = user_properties["USER_TIMEZONE"]
        user_timezone = timezones.tz_label_to_timezone(user_timezone)
    else:
        user_timezone = timezones.tz_label_to_timezone(constants.DEFAULT_USER_TIMEZONE)

    # Get all agent logs
    all_agent_logs = (
        AgentLog.query.filter_by(agent_id=agent_id).order_by(AgentLog.timestamp.desc()).all()
    )

    if current_user.subscribed:
        all_agent_logs_qry = AgentLog.query.filter_by(agent_id=agent_id).order_by(
            AgentLog.timestamp.desc()
        )
    else:
        all_agent_logs_qry = (
            AgentLog.query.filter_by(agent_id=agent_id)
            .order_by(AgentLog.timestamp.desc())
            .limit(constants.DEFAULT_AGENT_LOGS_PER_AGENT_FREE)
        )

    all_agent_logs = all_agent_logs_qry.all()

    return [log.to_dict(format_str, user_timezone) for log in all_agent_logs]


# A function to delete all logs for a given agent
def delete_all_agent_logs(agent_id: int) -> bool:
    # Get all agent logs
    all_agent_logs = AgentLog.query.filter_by(agent_id=agent_id).all()

    # Delete all agent logs
    try:
        for log in all_agent_logs:
            DATABASE.session.delete(log)
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error deleting agent logs: {e}")
        return False

    return True
