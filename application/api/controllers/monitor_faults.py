from flask_login import current_user

from application.common import logger, constants
from application.models.monitor import Monitor
from application.models.monitor_fault import MonitorFault
from application.extensions import DATABASE


def get_monitor_faults(agent_id: int, monitor_type: str) -> bool:
    monitor_obj = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type).first()

    if monitor_obj is None:
        logger.error(f"No monitor found for agent {agent_id} with type {monitor_type}")
        return {"status": f"Monitor Type {monitor_type} not found."}

    if "USER_HOUR_FORMAT" in current_user.properties:
        if current_user.properties["USER_HOUR_FORMAT"] == "12":
            time_format_str = constants.TIMESTAMP_FORMAT_12_HR
        else:
            time_format_str = constants.TIMESTAMP_FORMAT_24_HR
    else:
        time_format_str = constants.DEFAULT_TIME_FORMAT_STR

    active_faults = monitor_obj.faults(time_format_str=time_format_str)
    num_faults = len(active_faults)

    return {
        "num_faults": num_faults,
        "faults": active_faults,
        "status": "Success",
    }


def deactivate_monitor_fault(agent_id: int, monitor_type: str, fault_id: int) -> bool:
    monitor_obj = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type).first()

    if monitor_obj is None:
        logger.error(f"No monitor found for agent {agent_id} with type {monitor_type}")
        return False

    logger.info(f"Deactivating monitor fault {fault_id} for monitor {monitor_obj.monitor_id}")

    monitor_fault_qry = MonitorFault.query.filter_by(
        monitor_id=monitor_obj.monitor_id, monitor_fault_id=fault_id
    )

    if monitor_fault_qry.first() is None:
        logger.debug(
            f"No monitor fault found for monitor {monitor_obj.monitor_id} with fault {fault_id}"
        )
        return False

    # Set active False
    update_dict = {"active": False}

    monitor_fault_qry.update(update_dict)

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(
            f"Failed to deactivate monitor fault {fault_id} for monitor {monitor_obj.monitor_id}"
        )
        logger.error(e)
        return False

    # Now check if the monitor has any other active faults
    if len(monitor_obj.faults()) == 0:
        # If no active faults, set has_fault to False
        monitor_obj.has_fault = False
        DATABASE.session.commit()

    return True
