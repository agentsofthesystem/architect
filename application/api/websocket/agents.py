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
    )

    client_response = client.architect.get_agent_info()

    if client_response is None:
        logger.error("Contacted agent, but it did not respond.")
        response.update({"agent_info": "Error"})
    else:
        response.update({"agent_info": client_response})

    emit("respond_agent_info", response, json=True, namespace="/system/agent/info")


@SOCKETIO.on("get_action_result", namespace="/system/agent/info")
def get_action_result(input_dict):
    response = {}

    logger.info("Websocket GET ACTION RESULT... TRIGGERED!!!!")

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

    client_response = client.game.get_game_status(input_dict["game_name"])

    if client_response is None:
        logger.error("Contacted agent, but it did not respond.")
        response.update({"result": "Error"})
    else:
        response.update({"result": client_response})

    emit("respond_action_result", response, json=True, namespace="/system/agent/info")
