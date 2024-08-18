import pytz

from datetime import datetime, timezone, timedelta

from application.common import constants, logger, timezones
from application.extensions import DATABASE
from application.models.agent import Agents
from application.models.default_property import DefaultProperty
from application.models.group import Groups
from application.models.monitor import Monitor
from application.models.monitor_fault import MonitorFault
from application.models.setting import SettingsSql
from application.models.user import UserSql


# Add a user to a list if they are not already in the list.
def _add_user_to_list(user_id: int, user_list: list) -> list:
    if user_id not in user_list:
        user_list.append(user_id)
    return user_list


# Get user object from Id
def _get_user_object(user_id: int) -> list:
    return UserSql.query.filter_by(user_id=user_id).first()


# Convert the list of user IDs to a list of user objects
def _get_user_objects(user_ids: list) -> list:
    return DATABASE.session.query(UserSql).filter(UserSql.user_id.in_(user_ids)).all()


# Get the monitor object from the monitor_id
def _get_monitor_obj(monitor_id: int) -> Monitor:
    return Monitor.query.filter_by(monitor_id=monitor_id).first()


# Specifically get the agent's health monitor object from the agent_id
def _get_agent_health_monitor_obj(agent_id: int) -> Monitor:
    return Monitor.query.filter_by(
        agent_id=agent_id,
        monitor_type=constants.monitor_type_to_string(constants.MonitorTypes.AGENT),
    ).first()


# Get the agent object from the agent_id
def _get_agent_obj(agent_id: int) -> Agents:
    return Agents.query.filter_by(agent_id=agent_id).first()


# Get the owner of the monitor.
def _get_monitor_owner(monitor_id: int) -> UserSql:
    monitor_obj = _get_monitor_obj(monitor_id)
    agent_obj = _get_agent_obj(monitor_obj.agent_id)
    return _get_user_object(agent_obj.owner_id)


# Get the value of a user preference based on the user_id and preference name.
def get_user_property(user_id: int, property_name: str) -> str:
    user_obj = _get_user_object(user_id)
    user_properties = user_obj.properties
    property_value = None

    if property_name in user_properties:
        property_value = user_properties[property_name]
    else:
        # Property value is the default value if it is not found in the user properties.
        default_property = DefaultProperty.query.filter_by(property_name=property_name).first()
        property_value = default_property.property_default_value

    return property_value


# Determine if the admin put the system in testing mode for monitors.
def is_monitor_testing_enabled() -> bool:
    setting = SettingsSql.query.filter_by(name="MONITOR_TEST_MODE").first()
    setting_test = setting.value.lower()
    return True if setting_test == "true" else False


# Check if the attribute string representation of a bool is True or False
def is_attribute_true(monitor: Monitor, attribute: str) -> bool:
    if not has_monitor_attribute(monitor, attribute):
        return False
    attribute_value = monitor.attributes[attribute]
    return True if attribute_value.lower() == "true" else False


# Determine whether or not the monitor has an attribute.
def has_monitor_attribute(monitor: Monitor, attribute: str) -> bool:
    return True if attribute in monitor.attributes else False


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


# Update the monitor object task_id field.
def update_monitor_task_id(monitor_id: int, task_id: str) -> None:
    monitor = Monitor.query.filter_by(monitor_id=monitor_id).first()
    monitor.task_id = task_id

    try:
        DATABASE.session.commit()
    except Exception as e:
        DATABASE.session.rollback()
        raise e


# Update the Monitor object next_check and last_check fields.
def update_monitor_check_times(monitor_id: int, is_stopped=False) -> None:
    monitor = Monitor.query.filter_by(monitor_id=monitor_id).first()

    if is_monitor_testing_enabled():
        interval = constants.DEFAULT_MONITOR_TESTING_INTERVAL
    else:
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


# Check database for a matching, active, fault with the same description.
def is_fault_description_matching(monitor_id: int, fault_description: str) -> bool:
    fault_obj = MonitorFault.query.filter_by(
        monitor_id=monitor_id, fault_description=fault_description, active=True
    ).first()

    return True if fault_obj is not None else False


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


# A function to group function calls.  Throw faults and bail out.
def add_fault_and_disable(monitor_id: int, fault_string: str) -> None:

    # Create the fault object
    create_monitor_fault(monitor_id, fault_string)

    # Set the fault flag
    set_monitor_fault_flag(monitor_id, has_fault=True)

    # Update the monitor check times
    update_monitor_check_times(monitor_id, is_stopped=True)

    # Null out the task id. Not coming back until user turns back on.
    update_monitor_task_id(monitor_id, None)

    # Disabled the monitor automatically
    disable_monitor(monitor_id)


# Determine whether or not the current time is within the maintenance window.
def is_inside_maintenance_hour(maintenance_hour: int, user_timezone_label: str) -> bool:
    # Write a function that returns a timezone based on UTC offset.
    user_timezone = timezones.tz_label_to_timezone(user_timezone_label)
    pytz_timezone = pytz.timezone(user_timezone)

    now = datetime.now(pytz_timezone)

    start_hour = datetime(now.year, now.month, now.day, maintenance_hour, 00)
    end_hour = start_hour + timedelta(hours=1)

    maintenance_hour_start = pytz_timezone.localize(start_hour)
    maintenance_hour_end = pytz_timezone.localize(end_hour)

    logger.debug(f"Desired timezone: {pytz_timezone}")
    logger.debug(f"Current time: {now}")
    logger.debug(f"Maintenance start time: {maintenance_hour_start}")
    logger.debug(f"Maintenance end time: {maintenance_hour_end}")

    return True if now >= maintenance_hour_start and now < maintenance_hour_end else False
