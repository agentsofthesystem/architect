from flask_login import current_user
from flask_socketio import emit

from application.common import logger
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

    # Get Monitor record
    monitor_obj = Monitor.query.filter_by(
        agent_id=input_dict["agent_id"], monitor_type=input_dict["monitor_type"]
    ).first()

    if monitor_obj is None:
        logger.critical("Monitor not found")
        response.update({"status": "Error"})
    else:
        monitor_dict = monitor_obj.to_dict()

        # These are datetime objects
        next_check = monitor_dict["next_check"]
        last_check = monitor_dict["last_check"]

        user_properties = current_user.properties

        if "USER_TIMEZONE" in user_properties:
            user_timezone = user_properties["USER_TIMEZONE"]
            logger.debug(f"User's timezone is {user_timezone}")

        # TODO - Convert this to user's preference timezone.
        if next_check is not None:
            next_check_time_str = next_check.strftime("%m/%d/%Y, %H:%M:%S")
            monitor_dict["next_check"] = next_check_time_str

        if last_check is not None:
            last_check_time_str = last_check.strftime("%m/%d/%Y, %H:%M:%S")
            monitor_dict["last_check"] = last_check_time_str

        response.update(
            {"monitor": monitor_dict, "attributes": {}, "faults": {}, "status": "Success"}
        )

        attributes = monitor_obj.attributes
        for key, value in attributes.items():
            response["attributes"].update({key: value})

        for fault in monitor_obj.faults:
            response["faults"].update({fault["name"]: fault})

    emit("respond_monitor_status", response, json=True, namespace="/system/agent/monitor")
