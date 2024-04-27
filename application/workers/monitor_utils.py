from datetime import datetime, timezone, timedelta

from application.common import constants, logger
from application.extensions import DATABASE
from application.models.agent import Agents
from application.models.group import Groups
from application.models.monitor import Monitor
from application.models.monitor_fault import MonitorFault
from application.models.setting import SettingsSql
from application.models.user import UserSql


# Determine if the admin put the system in testing mode for monitors.
def is_monitor_testing_enabled() -> bool:
    setting = SettingsSql.query.filter_by(name="MONITOR_TEST_MODE").first()
    setting_test = setting.value.lower()
    return True if setting_test == "true" else False


# Update Monitor object to disable the monitor.
def disable_monitor(monitor_id: int) -> None:
    monitor = Monitor.query.filter_by(monitor_id=monitor_id).first()

    monitor.active = False

    try:
        DATABASE.session.commit()
    except Exception as e:
        DATABASE.session.rollback()
        raise e


# Set the fault flag on the monitor.
def set_monitor_fault_flag(monitor_id: int, has_fault: bool) -> None:
    monitor = Monitor.query.filter_by(monitor_id=monitor_id).first()
    monitor.has_fault = has_fault

    try:
        DATABASE.session.commit()
    except Exception as e:
        DATABASE.session.rollback()
        raise e


# Determine whether or not the monitor has an attribute.
def has_monitor_attribute(monitor: Monitor, attribute: str) -> bool:
    return True if attribute in monitor.attributes else False


# Update the Monitor object next_check and last_check fields.
def update_monitor_check_times(monitor_id: int, is_stopped=False) -> None:
    monitor = Monitor.query.filter_by(monitor_id=monitor_id).first()

    if has_monitor_attribute(monitor, "interval"):
        interval = int(monitor.attributes["interval"])
    else:
        interval = constants.DEFAULT_MONITOR_INTERVAL

    monitor.last_check = datetime.now(timezone.utc)

    # If there is not going to be a next check, set the next_check field to None.
    if not is_stopped:
        monitor.next_check = datetime.now(timezone.utc) + timedelta(seconds=interval)
    else:
        monitor.next_check = None

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Error updating monitor check times: {e}")
        DATABASE.session.rollback()


# Create a MonitorFault object and add it to the database.
def create_monitor_fault(monitor_id: int, fault: str) -> None:
    new_fault = MonitorFault(
        monitor_id=monitor_id,
        fault_time=datetime.now(timezone.utc),
        active=True,
        fault_description=fault,
    )

    try:
        DATABASE.session.add(new_fault)
        DATABASE.session.commit()
    except Exception as e:
        DATABASE.session.rollback()
        raise e


# Add a user to a list if they are not already in the list.
def _add_user_to_list(user_id: int, user_list: list) -> list:
    if user_id not in user_list:
        user_list.append(user_id)
    return user_list


# Convert the list of user IDs to a list of user objects
def _get_user_objects(user_ids: list) -> list:
    return DATABASE.session.query(UserSql).filter(UserSql.user_id.in_(user_ids)).all()


# Get a list of all users that have access to the agent via groups or friendship.
def get_agent_users(agent_id: int, return_objects=False) -> list:
    agent = Agents.query.filter_by(agent_id=agent_id).first()

    if agent is None:
        return []

    agent_users = []

    # Get all groups that the agent is a member of
    agent_group_members = agent.groups_with_access.all()

    for member in agent_group_members:
        group_member_id = member.group_member_id
        group_obj = Groups.query.filter_by(group_id=group_member_id).first()
        group_members = group_obj.members.all()

        for member in group_members:
            agent_users = _add_user_to_list(member.member_id, agent_users)

    # Get all friends of the agent
    friend_members = agent.friends_with_access.all()

    for member in friend_members:
        agent_users = _add_user_to_list(member.friend_member_id, agent_users)

    if return_objects:
        return _get_user_objects(agent_users)
    else:
        return agent_users
