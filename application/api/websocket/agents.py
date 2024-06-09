"""
This module shall contain all agent related web sockets.

Docs:
1. https://flask-socketio.readthedocs.io/en/latest/getting_started.html
2. https://socket.io/docs/v3/listening-to-events/

"""

from flask import current_app
from flask_socketio import emit

from application.common import logger, toolbox
from application.extensions import SOCKETIO
from application.models.agent import Agents
from application.models.user import UserSql

from operator_client import Operator


@SOCKETIO.on("message")
def handle_message(data):
    print("received message: " + data)


@SOCKETIO.on("get_agent_status", namespace="/system/agents")
def get_agent_status(input_dict):
    response = {}

    if "agent_id" not in input_dict:
        logger.critical("Agent ID not provided... cannot contact agent.")
        response.update({"status": "Unreachable"})

    response.update({"agent_id": input_dict["agent_id"]})

    agent_obj = Agents.query.filter_by(agent_id=input_dict["agent_id"]).first()

    if agent_obj is None:
        logger.critical("Agent ID Does not exist... cannot contact agent.")
        response.update({"status": "Error"})

    hostname = toolbox.format_url_prefix(agent_obj.hostname)

    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    client = Operator(
        hostname,
        agent_obj.port,
        verbose,
        token=agent_obj.access_token,
        certificate=agent_obj.ssl_public_cert,
    )

    client_response = client.architect.get_health(secure_version=True)

    if client_response is None:
        logger.error("Contacted agent, but it did not respond.")
        response.update({"status": "Unreachable"})
    else:
        response.update({"status": client_response})

    emit("respond_agent_status", response, json=True, namespace="/system/agents")


@SOCKETIO.on("get_agent_info", namespace="/system/agent/info")
def get_agent_info(input_dict):
    response = {}

    if "agent_id" not in input_dict:
        logger.critical("Agent ID not provided... cannot contact agent.")
        response.update({"status": "Unreachable"})

    response.update({"agent_id": input_dict["agent_id"]})

    agent_obj = Agents.query.filter_by(agent_id=input_dict["agent_id"]).first()
    owner_obj = UserSql.query.filter_by(user_id=agent_obj.owner_id).first()

    if agent_obj is None:
        logger.critical("Agent ID Does not exist... cannot contact agent.")
        response.update({"agent_info": "Error"})

    hostname = toolbox.format_url_prefix(agent_obj.hostname)

    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    client = Operator(
        hostname,
        agent_obj.port,
        verbose,
        token=agent_obj.access_token,
        certificate=agent_obj.ssl_public_cert,
        timeout=10,
    )

    client_response = client.architect.get_agent_info()

    if client_response is None:
        logger.error("Contacted agent, but it did not respond.")
        response.update({"agent_info": "Error"})
    else:
        # Limit the games list to one, if there is at least one object in the list.
        if not owner_obj.subscribed and len(client_response["games"]) > 1:
            client_response["games"] = client_response["games"][:1]

        response.update({"agent_info": client_response})

    emit("respond_agent_info", response, json=True, namespace="/system/agent/info")


@SOCKETIO.on("get_action_result", namespace="/system/agent/info")
def get_action_result(input_dict):
    response = {}

    if "agent_id" not in input_dict:
        logger.critical("Agent ID not provided...")
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    if "action" not in input_dict:
        logger.critical("Action not provided...")
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    if "game_name" not in input_dict:
        logger.critical("Game Server Name not provided...")
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    if "attempt_number" not in input_dict:
        logger.critical("Need to know which attempt this is...")
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    response.update(
        {
            "agent_id": input_dict["agent_id"],
            "action": input_dict["action"],
            "game_name": input_dict["game_name"],
            "attempt_number": input_dict["attempt_number"],
        }
    )

    command_action = input_dict["action"]
    game_name = input_dict["game_name"]

    # Ensure the command action supplied is valid.
    if command_action not in ["startup", "shutdown", "restart", "update"]:
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    agent_obj = Agents.query.filter_by(agent_id=input_dict["agent_id"]).first()

    if agent_obj is None:
        logger.critical("Agent ID Does not exist... cannot contact agent.")
        response.update({"result": "Error"})
        emit("respond_action_result", response, json=True, namespace="/system/agent/info")
        return

    hostname = toolbox.format_url_prefix(agent_obj.hostname)

    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    client = Operator(
        hostname,
        agent_obj.port,
        verbose,
        token=agent_obj.access_token,
        certificate=agent_obj.ssl_public_cert,
    )

    if command_action in ["startup", "shutdown", "restart"]:
        client_response = client.game.get_game_status(input_dict["game_name"])

        if client_response is None:
            logger.error("Contacted agent, but it did not respond.")
            response.update({"result": "Error"})
        else:
            response.update({"result": client_response})
    else:
        client_response = client.game.get_game_by_name(input_dict["game_name"])
        action = client_response["actions"][0]
        if action["type"] != "updating":
            response.update({"result": "Error"})
        else:
            thread_ident = action["result"]
            thread_alive = client.app.is_thread_alive(thread_ident)
            update_state = {"status": "updating"} if thread_alive else {"status": "complete"}

            if not thread_alive:
                # Get the game now, that it's been updated, and update the agent so that it
                # knows what the current build id is.
                game_data = client.game.get_game_by_name(game_name)
                game_id = game_data["items"][0]["game_id"]
                steam_id = game_data["items"][0]["game_steam_id"]
                game_install_path = game_data["items"][0]["game_install_dir"]
                steam_install_dir = client.app.get_setting_by_name("steam_install_dir")

                steam_build_id = client.steam.get_steam_app_build_id(
                    steam_install_dir, game_install_path, steam_id
                )

                if steam_build_id:
                    client.game.update_game_data(game_id, game_steam_build_id=steam_build_id)

            response.update({"result": update_state})

    emit("respond_action_result", response, json=True, namespace="/system/agent/info")
