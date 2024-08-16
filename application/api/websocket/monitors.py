from flask_login import current_user
from flask_socketio import emit

from application.common import logger, constants, timezones
from application.extensions import SOCKETIO
from application.models.monitor import Monitor


@SOCKETIO.on("get_monitor_status", namespace="/system/agent/monitor")
def get_monitor_status(input_dict):
    logger.debug(f"Received get_monitor_status request: {input_dict}")

    response = {}

    if "agent_id" not in input_dict:
        logger.critical("Agent ID not provided... cannot contact agent.")
        response.update({"status": "Error"})

    if "monitor_type" not in input_dict:
        logger.critical("Monitor type not provided... cannot contact agent.")
        response.update({"status": "Error"})

    if not hasattr(current_user, "properties"):
        logger.critical("User properties not found.")
        response.update({"status": "Error"})

    agent_id = input_dict["agent_id"]
    monitor_type = input_dict["monitor_type"]

    # Get Monitor record
    monitor_obj = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type).first()

    if monitor_obj is None:
        logger.critical(f"Monitor Type, {monitor_type} does not exist for agent id: {agent_id}")
        response.update({"status": "Error"})
    else:
        monitor_dict = monitor_obj.to_dict()

        # These are datetime objects
        next_check = monitor_dict["next_check"]
        last_check = monitor_dict["last_check"]

        # User properties to determine whether or not to apply offset
        user_properties = current_user.properties
        format_str = timezones._apply_time_format_preference(user_properties)
        offset_available = False

        if "USER_TIMEZONE" in user_properties:
            user_timezone = user_properties["USER_TIMEZONE"]
            user_offset = timezones._get_timezone_offset(user_timezone)
            offset_available = True
        else:
            user_timezone = constants.DEFAULT_USER_TIMEZONE
            user_offset = 0

        logger.debug(f"User's timezone is {user_timezone}, offset: {user_offset}")

        if next_check is not None:
            if offset_available:
                next_check = timezones._apply_offset_to_datetime(next_check, user_offset)
            next_check_time_str = next_check.strftime(format_str)
            monitor_dict["next_check"] = next_check_time_str

        if last_check is not None:
            if offset_available:
                last_check = timezones._apply_offset_to_datetime(last_check, user_offset)
            last_check_time_str = last_check.strftime(format_str)
            monitor_dict["last_check"] = last_check_time_str

        response.update(
            {"monitor": monitor_dict, "attributes": {}, "faults": {}, "status": "Success"}
        )

        # Set to empty dictionaries.
        response["attributes"] = {}
        response["faults"] = {}

        attributes = monitor_obj.attributes
        for key, value in attributes.items():
            response["attributes"].update({key: value})

        # In the event, no attribute exists for interval, then set the default.
        if "interval" not in response["attributes"]:
            response["attributes"].update({"interval": constants.DEFAULT_MONITOR_INTERVAL})

        for fault in monitor_obj.faults(time_format_str=format_str):
            response["faults"].update({fault["name"]: fault})

    emit("respond_monitor_status", response, json=True, namespace="/system/agent/monitor")
