from datetime import datetime, timezone

from application.api.controllers import messages
from application.common import logger, constants, toolbox
from application.extensions import CELERY
from application.workers import monitor_constants, monitor_utils
from operator_client import Operator


@CELERY.task(bind=True)
def agent_health_monitor(self, monitor_id: int):
    logger.debug(f"Agent Health Monitor Task Running at {datetime.now(timezone.utc)}")

    monitor_obj = monitor_utils._get_monitor_obj(monitor_id)
    monitor_active = False

    if monitor_obj is None:
        logger.error(f"Monitor ID {monitor_id} not found.")
        self.update_state(state="FAILURE")
        return {"status": "Monitor ID not found."}

    monitor_active = monitor_obj.active

    if not monitor_active:
        logger.error(f"Monitor ID {monitor_id} - Monitor Not Active.")
        logger.debug("This means the monitor was disabled since the last run.")
        self.update_state(state="FAILURE")
        return {"status": "Monitor Not Active."}

    # Compare the task_id to the task_id in the monitor object. If they do not match, then
    # this task is stale and should be revoked.
    if monitor_obj.task_id != self.request.id:
        logger.error(
            f"Monitor ID {monitor_id} - "
            f"Task ID Mismatch: {monitor_obj.task_id} != {self.request.id}"
        )
        logger.debug("This means the container restarted and the revoked task list reset.")
        self.update_state(state="FAILURE")
        return {"status": "Task ID Mismatch."}

    # Get the agent object associated with the monitor
    agent_obj = monitor_utils._get_agent_obj(monitor_obj.agent_id)

    if agent_obj is None:
        logger.error(f"Agent ID {monitor_obj.agent_id} not found.")
        self.update_state(state="FAILURE")
        return {"status": "Agent ID not found."}

    # Get the owner associated with the monitor
    owner_obj = monitor_utils._get_monitor_owner(monitor_obj.monitor_id)

    logger.debug(f"Agent Health Monitor owned by: {owner_obj.username}({owner_obj.user_id})")

    if monitor_utils.is_monitor_testing_enabled():
        logger.debug("Monitor Testing is enabled. Using Default Test Interval Constant.")
        next_interval = constants.DEFAULT_MONITOR_TESTING_INTERVAL
    else:
        if monitor_utils.has_monitor_attribute(monitor_obj, "interval"):
            next_interval = int(monitor_obj.attributes["interval"])
        else:
            next_interval = constants.DEFAULT_MONITOR_INTERVAL

    if monitor_utils.has_monitor_attribute(monitor_obj, "alert_enable"):
        alert_enable = monitor_utils.is_attribute_true(monitor_obj, "alert_enable")
    else:
        alert_enable = False

    logger.debug(f"Next Interval: {next_interval} seconds, and Alert Users: {alert_enable}")

    # Create a client to communicate with the agent
    client = Operator(
        toolbox.format_url_prefix(agent_obj.hostname),
        agent_obj.port,
        verbose=False,
        token=agent_obj.access_token,
        certificate=agent_obj.ssl_public_cert,
        timeout=constants.AGENT_SMITH_TIMEOUT,
    )

    # Get the health status of the agent
    health_status = client.architect.get_health(secure_version=True)
    fault_string = f"Health Check Failed: {health_status}"

    if monitor_utils.is_fault_description_matching(monitor_obj.monitor_id, fault_string):
        logger.debug("Fault already exists for this Agent. Skipping.")
        monitor_active = False
        self.update_state(state="SUCCESS")
        return {"status": "Agent has fault already."}

    # If a fault is detected, create a fault object. Alert the users if the alert is enabled.
    # Also, disable the monitor.
    if health_status in constants.AGENT_SMITH_INVALID_HEALTH:
        logger.error(f"Agent ID {agent_obj.agent_id} - Detected Invalid Status: {health_status}")

        if health_status is None:
            health_status = "Unreachable Agent."

        monitor_utils.add_fault_and_disable(monitor_obj.monitor_id, fault_string)
        monitor_active = False

        # Email users attached to agent.
        if alert_enable:
            logger.debug(f"Alerting users for Agent ID {agent_obj.agent_id}")
            user_list = monitor_utils.get_agent_users(agent_obj.agent_id)

            subject = monitor_constants.ALERT_MESSAGES_FMT_STR["AGENT"]["subject"].format(
                hostname=agent_obj.hostname
            )
            message = monitor_constants.ALERT_MESSAGES_FMT_STR["AGENT"]["message"].format(
                hostname=agent_obj.hostname, health_status=health_status
            )

            # The message sender_id shall be the owner of the agent.
            messages.message_user_list(
                agent_obj.owner_id, user_list, message, subject, constants.MessageCategories.MONITOR
            )

        self.update_state(state="SUCCESS")
        return {"status": "Invalid Health Status."}

    else:
        logger.debug(f"Agent ID {agent_obj.agent_id} - Health Status: {health_status} - Healthy!")

    if monitor_active:
        logger.debug(f"Monitor ID {monitor_id} is active. Scheduling next health check.")
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id)
        new_task = self.apply_async(
            [monitor_id],
            countdown=next_interval,
        )
        monitor_utils.update_monitor_task_id(monitor_obj.monitor_id, new_task.id)
    else:
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id, is_stopped=True)
        monitor_utils.update_monitor_task_id(monitor_obj.monitor_id, None)
        logger.debug(f"Monitor ID {monitor_id} is not active. Stopping further health checks..")

    self.update_state(state="SUCCESS")
    return {"status": "Task Completed!"}
