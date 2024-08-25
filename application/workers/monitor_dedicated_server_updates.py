from datetime import datetime, timezone

from application.api.controllers import messages
from application.api.controllers.agent_logs import create_agent_log
from application.common import logger, constants, toolbox
from application.extensions import CELERY
from application.workers import monitor_constants, monitor_utils
from application.workers import monitor_server_utils
from operator_client import Operator


@CELERY.task(bind=True)
def dedicated_server_update_monitor(self, monitor_id: int):
    logger.debug(f"Dedicated Server Update Monitor Task Running at {datetime.now(timezone.utc)}")

    monitor_obj = monitor_utils._get_monitor_obj(monitor_id)
    owner_id = None
    final_server_state = None
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

    # This cannot be None because the monitor record is created at the time of agent creation.
    agent_health_monitor = monitor_utils._get_agent_health_monitor_obj(agent_obj.agent_id)

    # Get the owner associated with the monitor
    owner_obj = monitor_utils._get_monitor_owner(monitor_obj.monitor_id)

    logger.debug(f"Agent Health Monitor owned by: {owner_obj.username}({owner_obj.user_id})")

    # Get the owner's maintenance window preference or assume the default.
    owner_id = agent_obj.owner_id
    maintenance_hour = monitor_utils.get_user_property(owner_id, "USER_MAINTENANCE_HOUR")
    user_tz_label = monitor_utils.get_user_property(owner_id, "USER_TIMEZONE")

    if monitor_utils.has_monitor_attribute(monitor_obj, "final_server_state"):
        final_server_state_str = monitor_obj.attributes["final_server_state"]
        final_server_state = constants.server_state_from_string(final_server_state_str)
    else:
        final_server_state = constants.ServerStates.SAME

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

    # If the agent health monitor has a fault... back out now.
    if agent_health_monitor.has_fault:
        fault_string = "Agent Health Monitor has detected a fault. Disabling this monitor."
        logger.error(fault_string)
        self.update_state(state="FAILURE")

        if monitor_utils.is_fault_description_matching(monitor_obj.monitor_id, fault_string):
            logger.debug("Fault already exists for this Agent. Skipping.")
        else:
            monitor_utils.add_fault_and_disable(monitor_obj.monitor_id, fault_string)

        monitor_active = False
        return {"status": "Agent Health Monitor Fault."}

    # Get the health status of the agent
    health_status = client.architect.get_health(secure_version=True)

    # If a fault is detected, create a fault object. Alert the users if the alert is enabled.
    # Also, disable the monitor.
    if health_status in constants.AGENT_SMITH_INVALID_HEALTH:
        logger.error(f"Agent ID {agent_obj.agent_id} - Detected Invalid Status: {health_status}")

        if health_status is None:
            health_status = "Unreachable Agent."

        fault_string = f"Health Check Failed: {health_status}"

        if monitor_utils.is_fault_description_matching(monitor_obj.monitor_id, fault_string):
            logger.debug("Fault already exists for this Agent. Skipping.")
        else:
            monitor_utils.add_fault_and_disable(monitor_obj.monitor_id, fault_string)

        monitor_active = False

        self.update_state(state="SUCCESS")
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

        alert_fmt_str_list = []  # One or more possible total message

        # Loop through all the servers and check if they are running, and take actions if necessary.
        for server in installed_servers:
            server_id = server["game_id"]
            server_name = server["game_name"]
            server_pid = server["game_pid"]
            fault_string_1 = f"Server {server_name} requires an update."
            fault_string_2 = f"Server {server_name} was updated."
            fault_string_3 = f"Server {server_name} will be updated at the next maintenance window."

            # Check if the server requires an update, it does not have to be running to do this.
            update_info = client.game.check_for_update(server_id)

            if update_info is None:
                logger.error(f"Server {server_name} - Update Check Failed.")
                continue

            is_required = update_info["is_required"]
            current_version = update_info["current_version"]
            target_version = update_info["target_version"]

            # Package input into dict for emails later, if needed.
            alert_fmt_inputs = {}
            alert_fmt_inputs["server_name"] = server_name
            alert_fmt_inputs["current_version"] = current_version
            alert_fmt_inputs["target_version"] = target_version
            alert_fmt_inputs["format_string_dict"] = {}

            logger.debug(
                f"Server {server_name} - Current Version: {current_version}, "
                f"Target Version: {target_version}, Update Required: {is_required}"
            )

            if is_required:

                # If the user has enabled auto-restart, then the server will be stopped, updated,
                # and restarted.
                if monitor_utils.has_monitor_attribute(monitor_obj, "server_auto_update"):
                    logger.debug(f"Server {server_name} - Auto-Update Enabled.")

                    logger.debug(
                        f"Checking if inside maintenance hour: {maintenance_hour}, "
                        f":TZ: {user_tz_label}"
                    )

                    if not monitor_utils.is_inside_maintenance_hour(
                        maintenance_hour, user_tz_label
                    ):
                        logger.debug("Outside Maintenance Window. Skipping Server Update.")

                        if monitor_utils.is_fault_description_matching(
                            monitor_obj.monitor_id, fault_string_3
                        ):
                            logger.debug(
                                f"This monitor has already alerted that update is coming in next "
                                f"maintenance window: {server_name}."
                            )
                            continue

                        monitor_utils.create_monitor_fault(monitor_obj.monitor_id, fault_string_3)
                        monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)
                        alert_fmt_inputs["format_string_dict"] = (
                            monitor_constants.ALERT_MESSAGES_FMT_STR["DS_UPDATE_3"]
                        )
                        alert_fmt_str_list.append(alert_fmt_inputs)
                    else:
                        logger.debug("Inside Maintenance Window. Updating Server.")

                        if monitor_utils.is_fault_description_matching(
                            monitor_obj.monitor_id, fault_string_2
                        ):
                            logger.debug(
                                "This monitor as already attempted to update "
                                f"server: {server_name}."
                            )
                            continue

                        # Prior to startup, is the server running?
                        is_server_running = monitor_server_utils._is_server_running(
                            client, server_pid, server_name
                        )

                        # Run shutdown subroutine - If server is already offline, can't hurt to do
                        # this anyway.
                        shutdown_result = monitor_server_utils._stop_server(client, server_name)

                        # Now issue the update command.
                        update_result = monitor_server_utils._update_server(client, server_name)

                        # Finally, startup the server.
                        if final_server_state == constants.ServerStates.ONLINE:
                            # User wants final state to be online no matter what.
                            startup_result = monitor_server_utils._start_server(client, server_name)
                        elif (
                            final_server_state == constants.ServerStates.SAME and is_server_running
                        ):
                            # Server was running to begin with and user wants it to resume its
                            # last state, so start it back up.
                            startup_result = monitor_server_utils._start_server(client, server_name)
                        else:
                            startup_result = False

                        logger.debug(
                            f"Server {server_name} - Shutdown: {shutdown_result}, "
                            f"Update: {update_result}, Startup: {startup_result}"
                        )

                        # Set the fault flag on the monitor overall.
                        monitor_utils.create_monitor_fault(monitor_obj.monitor_id, fault_string_2)
                        monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)
                        alert_fmt_inputs["format_string_dict"] = (
                            monitor_constants.ALERT_MESSAGES_FMT_STR["DS_UPDATE_2"]
                        )
                        alert_fmt_str_list.append(alert_fmt_inputs)

                        log_message = f"Monitor: Auto-Update: {server_name}"
                        create_agent_log(
                            agent_obj.owner_id, agent_obj.agent_id, log_message, is_automated=True
                        )

                # Otherwise, the user has not enabled auto-Update, and the server is left alone.
                # Only create a fault/alert.
                else:
                    logger.debug(f"Server {server_name} - Auto-Update Disabled.")

                    # This prevents spamming the same fault/action over and over.
                    if monitor_utils.is_fault_description_matching(
                        monitor_obj.monitor_id, fault_string_1
                    ):
                        logger.debug(
                            f"This monitor as already identified the server: {server_name}. "
                            "Needs an update."
                        )
                        continue

                    # The server is not running, and the user has not enabled auto-Update.
                    # Therefore, create a fault and alert the user.
                    monitor_utils.create_monitor_fault(monitor_obj.monitor_id, fault_string_1)

                    # Set the fault flag on the monitor overall.
                    monitor_utils.set_monitor_fault_flag(monitor_obj.monitor_id, has_fault=True)
                    alert_fmt_inputs["format_string_dict"] = (
                        monitor_constants.ALERT_MESSAGES_FMT_STR["DS_UPDATE_1"]
                    )
                    alert_fmt_str_list.append(alert_fmt_inputs)

        # Send alert to users, if enabled and a format str was set.
        if alert_enable and len(alert_fmt_str_list) > 0:
            user_list = monitor_utils.get_agent_users(agent_obj.agent_id)
            subject = f"Server Update Required: {agent_obj.hostname}"
            message = f"<p><h3>Agent: {agent_obj.hostname}</h3></p>"

            # Only send one email combined.
            for alert in alert_fmt_str_list:
                message += alert["format_string_dict"]["message"].format(
                    game_name=alert["server_name"],
                    current_version=alert["current_version"],
                    target_version=alert["target_version"],
                )
                message += "<p>************************************</p>"

            # The message sender_id shall be the owner of the agent.
            messages.message_user_list(
                agent_obj.owner_id,
                user_list,
                message,
                subject,
                constants.MessageCategories.MONITOR,
            )

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
