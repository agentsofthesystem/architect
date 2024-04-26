from datetime import datetime

from application.api.controllers import messages
from application.common import logger, constants, toolbox
from application.extensions import CELERY
from application.models.agent import Agents
from application.models.monitor import Monitor
from application.workers import monitor_utils
from operator_client import Operator


def _get_monitor_obj(monitor_id: int) -> Monitor:
    return Monitor.query.filter_by(monitor_id=monitor_id).first()


def _get_agent_obj(agent_id: int) -> Agents:
    return Agents.query.filter_by(agent_id=agent_id).first()


@CELERY.task(bind=True)
def run_agent_health_monitor(self, monitor_id: int):
    logger.debug(f"Agent Health Monitor Task Running at {datetime.now()}")
    self.update_state(state="SUCCESS")

    monitor_obj = _get_monitor_obj(monitor_id)

    if monitor_obj is None:
        logger.error(f"Monitor ID {monitor_id} not found.")
        return {"status": "Monitor ID not found."}

    # Get the agent object associated with the monitor
    agent_obj = _get_agent_obj(monitor_obj.agent_id)

    if agent_obj is None:
        logger.error(f"Agent ID {monitor_obj.agent_id} not found.")
        return {"status": "Agent ID not found."}

    if monitor_utils.is_monitor_testing_enabled():
        logger.debug("Monitor Testing is enabled. Using Default Test Interval Constant.")
        next_interval = constants.DEFAULT_MONITOR_TESTING_INTERVAL
    else:
        if monitor_utils.has_monitor_attribute(monitor_obj, "interval"):
            next_interval = int(monitor_obj.attributes["interval"])
        else:
            next_interval = constants.DEFAULT_MONITOR_INTERVAL

    alert_users = monitor_utils.has_monitor_attribute(monitor_obj, "alert_users")

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

    # These are the invalid statuses that can be returned from the agent. If Agent Smith ever
    # alters what these status are, then this will become broken.
    invalid_status = ["InvalidAccessToken", "SSLError", "SSLCertMissing", None]

    # If a fault is detected, create a fault object. Alert the users if the alert is enabled.
    # Also, disable the monitor.
    if health_status in invalid_status:
        logger.error(f"Agent ID {agent_obj.agent_id} - Detected Invalid Status: {health_status}")

        monitor_utils.create_monitor_fault(
            agent_obj.agent_id, monitor_obj.monitor_id, f"Health Check Failed: {health_status}"
        )

        # Set the fault flag
        monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)

        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id, is_stopped=True)

        # Disabled the monitor automatically
        monitor_utils.disable_monitor(monitor_obj.monitor_id)

        # Email users attached to agent.
        if alert_users:
            user_list = monitor_utils.get_agent_users(agent_obj.agent_id)
            subject = f"Agent Health Check Failed: {agent_obj.hostname}"
            message = f"Agent Health Check Failed: {health_status}"
            messages.message_user_list(
                user_list, message, subject, constants.MessageCategories.MONITOR
            )

        return {"status": "Invalid Health Status."}
    else:
        logger.debug(f"Agent ID {agent_obj.agent_id} - Health Status: {health_status} - Healthy!")

    if monitor_obj.active:
        logger.debug(f"Monitor ID {monitor_id} is active. Scheduling next health check.")
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id)
        self.apply_async(
            [monitor_id],
            countdown=next_interval,
        )
    else:
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id, is_stopped=True)
        logger.debug(f"Monitor ID {monitor_id} is not active. Stopping further health checks..")

    return {"status": "Task Completed!"}
