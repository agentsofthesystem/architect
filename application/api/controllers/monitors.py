from application.common import logger, constants
from application.extensions import DATABASE
from application.models.monitor import Monitor

from application.workers.agent_monitor import run_agent_health_monitor


def create_monitor(agent_id, monitor_type):
    logger.info(f"Creating monitor for agent {agent_id} with type {monitor_type}")

    monitor_qry = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type)
    monitor_obj = monitor_qry.first()
    monitor_type = constants.monitor_type_from_string(monitor_type)

    if monitor_obj is not None:
        logger.debug(f"Monitor already exists for agent {agent_id} with type {monitor_type}")
        # Update the monitor record to be active
        update_dict = {"active": True}
        monitor_qry.update(update_dict)
    else:
        # Create a new Monitor record
        monitor_obj = Monitor(
            agent_id=agent_id,
            monitor_type=monitor_type,
            active=True,
            interval=constants.DEFAULT_MONITOR_INTERVAL,
        )
        DATABASE.session.add(monitor_obj)

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to create monitor for agent {agent_id} with type {monitor_type}")
        logger.error(e)
        return False

    # Now kick off the monitor that was just created and/or enabled.
    if monitor_type == constants.MonitorTypes.AGENT:
        run_agent_health_monitor.apply_async([monitor_obj.monitor_id])
    else:
        logger.critical(f"Monitor type {monitor_type} not supported.")
        return False

    return True


def disable_monitor(agent_id, monitor_type):
    logger.info(f"Disabling monitor for agent {agent_id} with type {monitor_type}")

    monitor_qry = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type)

    if monitor_qry.first() is None:
        logger.debug(f"No monitor found for agent {agent_id} with type {monitor_type}")
        return False

    # Set active False, and next check is None because there will not be another check.
    update_dict = {"active": False, "next_check": None}

    monitor_qry.update(update_dict)

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to disable monitor for agent {agent_id} with type {monitor_type}")
        logger.error(e)
        return False

    return True
