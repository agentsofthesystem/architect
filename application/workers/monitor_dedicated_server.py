from datetime import datetime, timezone

from application.api.controllers import messages
from application.api.controllers.agent_logs import create_agent_log
from application.common import logger, constants, toolbox
from application.extensions import CELERY
from application.workers import monitor_constants, monitor_utils
from application.workers import monitor_server_utils
from operator_client import Operator


@CELERY.task(bind=True)
def dedicated_server_monitor(self, monitor_id: int):
    logger.debug(f"Dedicated Server Health Monitor Task Running at {datetime.now(timezone.utc)}")

    monitor_obj = monitor_utils._get_monitor_obj(monitor_id)
    alert_fmt_str = None

    if monitor_obj is None:
        logger.error(f"Monitor ID {monitor_id} not found.")
        return {"status": "Monitor ID not found."}

    # Compare the task_id to the task_id in the monitor object. If they do not match, then
    # this task is stale and should be revoked.
    if monitor_obj.task_id != self.request.id:
        logger.error(
            f"Monitor ID {monitor_id} - "
            f"Task ID Mismatch: {monitor_obj.task_id} != {self.request.id}"
        )
        logger.debug("This means the container restarted and the revoked task list reset.")
        return {"status": "Task ID Mismatch."}

    # Get the agent object associated with the monitor
    agent_obj = monitor_utils._get_agent_obj(monitor_obj.agent_id)

    if agent_obj is None:
        logger.error(f"Agent ID {monitor_obj.agent_id} not found.")
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

    # If a fault is detected, create a fault object. Alert the users if the alert is enabled.
    # Also, disable the monitor.
    if health_status in constants.AGENT_SMITH_INVALID_HEALTH:
        logger.error(f"Agent ID {agent_obj.agent_id} - Detected Invalid Status: {health_status}")

        if health_status is None:
            health_status = "Unreachable Agent."

        monitor_utils.create_monitor_fault(
            monitor_obj.monitor_id, f"Health Check Failed: {health_status}"
        )

        # Set the fault flag
        monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)

        # Update the monitor check times
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id, is_stopped=True)

        # Disabled the monitor automatically
        monitor_utils.disable_monitor(monitor_obj.monitor_id)

        return {"status": "Invalid Agent Health Status."}
    else:
        logger.debug(
            f"Agent ID {agent_obj.agent_id} - Health Status for (DS): {health_status} - Healthy!"
        )

        # Update the monitor check times
        monitor_utils.update_monitor_check_times(monitor_obj.monitor_id)

        # If the agent is healthy, then obtain all currently installed games on the agent.
        installed_servers = client.game.get_games()
        installed_servers = installed_servers["items"]  # This is the server list.

        # Loop through all the servers and check if they are running, and take actions if necessary.
        for server in installed_servers:
            server_pid = server["game_pid"]
            server_name = server["game_name"]
            fault_string = f"Server {server_name} is not running."

            # Get all active faults & skip if the fault already exists.  This prevents spamming
            # the same fault over and over.
            if monitor_utils.is_fault_description_matching(monitor_obj.monitor_id, fault_string):
                logger.debug(f"Fault already exists for this Server: {server_name}. Skipping.")
                continue

            logger.debug(f"Checking Server: {server_name} with PID: {server_pid}")

            # When the server_pid is not None, then the Agent is reporting that the server
            # SHOULD be running.
            if server_pid is not None:
                # Now, find out if the game is actually running.
                server_status = client.game.get_game_status(server_name)
                is_running = server_status["is_running"]

                logger.debug(f"Server {server_name} is running: {is_running}")

                # The server is not running
                if not is_running:
                    # Check and see if the user has enabled auto-restart.

                    # TODO - Potentially this could retry forever??? - Consider creating a fault
                    # anyway. This would prevent the monitor from spamming the user in the case
                    # where the automation attempts to restart the server and fails.
                    if monitor_utils.has_monitor_attribute(monitor_obj, "server_auto_restart"):
                        # Do not need to check value else because if the value is 'false', then the
                        # attribute does not exist. IF value is true then the attribute exists.
                        logger.debug(f"Auto-Restart is enabled for Server: {server_name}.")
                        logger.debug("Attempting to restart the server.")
                        result = monitor_server_utils._start_server(client, server_name)
                        logger.debug(f"Server Startup Result: {result}")
                        alert_fmt_str = monitor_constants.ALERT_MESSAGES_FMT_STR[
                            "DEDICATED_SERVER_1"
                        ]

                        log_message = f"Monitor: Auto-Restart: {server_name}"
                        create_agent_log(
                            agent_obj.owner_id, agent_obj.agent_id, log_message, is_automated=True
                        )

                    else:
                        # The server is not running, and the user has not enabled auto-restart.
                        # THerefore, create a fault and alert the user.
                        monitor_utils.create_monitor_fault(monitor_obj.monitor_id, fault_string)

                        # Set the fault flag on the monitor overall.
                        monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)

                        alert_fmt_str = monitor_constants.ALERT_MESSAGES_FMT_STR[
                            "DEDICATED_SERVER_2"
                        ]

            # Send alert to users, if enabled and a format str was set.
            if alert_enable and alert_fmt_str is not None:
                user_list = monitor_utils.get_agent_users(agent_obj.agent_id)
                subject = alert_fmt_str["subject"].format(hostname=agent_obj.hostname)
                message = alert_fmt_str["message"].format(
                    hostname=agent_obj.hostname, game_name=server_name
                )
                # The message sender_id shall be the owner of the agent.
                messages.message_user_list(
                    agent_obj.owner_id,
                    user_list,
                    message,
                    subject,
                    constants.MessageCategories.MONITOR,
                )

    if monitor_obj.active:
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

    return {"status": "Task Completed!"}
