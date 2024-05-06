"""This module houses constants specific to the monitor worker functions."""

# This is a dictionary containing the format strings for the alert messages that monitors will
# user. They are placed here to make it easier to change the messages in the future and minimize
# the amount of code in the monitor worker functions.
ALERT_MESSAGES_FMT_STR = {
    "AGENT": {
        "subject": "Agent Health Check Failed: {hostname}",
        "message": (
            "<p><h3>Agent: {hostname}</h3></p>"
            "<p>Agent Health Check Failed: {health_status}.</p>"
            "<p></p>"
            "<p>This monitor is now disabled and the Agent Must be re-connected.  A user"
            " must login and acknowledge the detected fault before resuming.</p>"
        ),
    },
    "DEDICATED_SERVER_1": {
        "subject": "Dedicated Server Health Check Failed: {hostname}",
        "message": (
            "<p><h3>Agent: {hostname}</h3></p>"
            "<p>Dedicated Server Health Check Failed: {game_name}.</p>"
            "<p></p>"
            "<p>This dedicated server was found to be offline when it should be online, and an"
            " attempt will be made to restart the server automatically.</p>"
        ),
    },
    "DEDICATED_SERVER_2": {
        "subject": "Dedicated Server Health Check Failed: {hostname}",
        "message": (
            "<p><h3>Agent: {hostname}</h3></p>"
            "<p>Dedicated Server Health Check Failed: {game_name}.</p>"
            "<p></p>"
            "<p>This dedicated server was found to be offline when it should be online. A user"
            " must manually restart the server.</p>"
        ),
    },
    "DS_UPDATE_1": {
        "subject": "Update Required: {hostname}",
        "message": (
            "<p><h3>Agent: {hostname}</h3></p>"
            "<p>Server: {game_name} requires an update.</p>"
            "<p></p>"
            "<p>Current Ver: {current_version}, Target Ver: {target_version}.</p>"
            "<p></p>"
            "<p>The server requires manual intervention to update.</p>"
        ),
    },
    "DS_UPDATE_2": {
        "subject": "Update Required: {hostname}",
        "message": (
            "<p><h3>Agent: {hostname}</h3></p>"
            "<p>Server: {game_name} requires an update.</p>"
            "<p></p>"
            "<p>The server will be stopped, updated, and restarted automatically.</p>"
        ),
    },
}

MAX_COMMAND_RETRIES = 6
COMMAND_WAIT_TIME = 10
