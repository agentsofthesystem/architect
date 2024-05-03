from application.common import logger, constants
from application.extensions import DATABASE, CELERY
from application.models.monitor import Monitor
from application.workers import celery_utils
from application.workers.agent_monitor import run_agent_health_monitor

_MONITOR_DEBUG = False


def create_monitor(agent_id, monitor_type):
    logger.info(f"Creating monitor for agent {agent_id} with type {monitor_type}")

    monitor_qry = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type)
    monitor_obj = monitor_qry.first()
    monitor_type_str = monitor_type
    monitor_type = constants.monitor_type_from_string(monitor_type)

    if monitor_obj is not None:
        logger.debug(f"Monitor already exists for agent {agent_id} with type {monitor_type_str}")

        # If the monitor has a fault, cannot set it to active..
        if monitor_obj.has_fault:
            logger.error(f"Monitor for agent {agent_id} with type {monitor_type_str} has a fault.")
            return False

        # Update the monitor record to be active
        update_dict = {"active": True}
        monitor_qry.update(update_dict)
    else:
        # Create a new Monitor record
        monitor_obj = Monitor(
            agent_id=agent_id,
            monitor_type=monitor_type_str,
            active=True,
            interval=constants.DEFAULT_MONITOR_INTERVAL,
        )
        DATABASE.session.add(monitor_obj)

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to create monitor for agent {agent_id} with type {monitor_type_str}")
        logger.error(e)
        return False

    monitor_id = monitor_obj.monitor_id

    if _MONITOR_DEBUG:
        active_tasks = CELERY.control.inspect().active()
        scheduled_tasks = CELERY.control.inspect().scheduled()
        logger.info("/////////////////////////////////////")
        logger.info("Enabling monitor..")
        logger.info(f"Active tasks: {active_tasks.items()}")
        logger.info(f"Scheduled tasks: {scheduled_tasks.items()}")
        logger.info("/////////////////////////////////////")

    new_task = None

    # Now kick off the monitor that was just created and/or enabled.
    if monitor_type == constants.MonitorTypes.AGENT:
        new_task = run_agent_health_monitor.apply_async([monitor_obj.monitor_id])

    else:
        logger.critical(f"Monitor type {monitor_type_str} not supported.")
        return False

    if new_task:
        try:
            monitor_obj.task_id = new_task.id
            DATABASE.session.commit()
        except Exception as e:
            logger.error(f"Failed to update task_id for monitor {monitor_id}")
            logger.error(e)
            DATABASE.session.rollback()
            return False
    else:
        logger.critical(f"Failed to create task for monitor {monitor_id}")
        return False

    return True


def disable_monitor(agent_id, monitor_type):
    logger.info(f"Disabling monitor for agent {agent_id} with type {monitor_type}")

    monitor_qry = Monitor.query.filter_by(agent_id=agent_id, monitor_type=monitor_type)
    monitor_obj = monitor_qry.first()
    monitor_type_str = monitor_type
    monitor_type = constants.monitor_type_from_string(monitor_type)

    if monitor_obj is None:
        logger.debug(f"No monitor found for agent {agent_id} with type {monitor_type_str}")
        return False

    if _MONITOR_DEBUG:
        active_tasks = CELERY.control.inspect().active()
        scheduled_tasks = CELERY.control.inspect().scheduled()
        logger.info("/////////////////////////////////////")
        logger.info("Disabling monitor..")
        logger.info(f"Active tasks: {active_tasks.items()}")
        logger.info(f"Scheduled tasks: {scheduled_tasks.items()}")
        logger.info("/////////////////////////////////////")

    monitor_id = monitor_obj.monitor_id
    task_id = monitor_obj.task_id

    if task_id is not None:
        celery_utils.revoke_task_by_id(task_id)
        logger.info(f"Revoking task {task_id} for monitor {monitor_id}")

    # Cleanup the monitor... the monitor might have been revoke while in the middle of
    # some operation. Check if the monitor has any active faults.
    has_fault = True if len(monitor_obj.faults) > 0 else False

    # Set active False, and next check is None because there will not be another check.
    update_dict = {"active": False, "next_check": None, "has_fault": has_fault, "task_id": None}

    monitor_qry.update(update_dict)

    try:
        DATABASE.session.commit()
    except Exception as e:
        logger.error(f"Failed to disable monitor for agent {agent_id} with type {monitor_type}")
        logger.error(e)
        return False

    return True
