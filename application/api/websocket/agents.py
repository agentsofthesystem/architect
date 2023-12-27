"""
This module shall contain all agent related web sockets.

Docs:
1. https://flask-socketio.readthedocs.io/en/latest/getting_started.html
2. https://socket.io/docs/v3/listening-to-events/

"""
from flask import current_app
from flask_socketio import emit

from application.common import logger, tools
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

    hostname = tools.format_url(agent_obj.hostname)

    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    client = Operator(hostname, agent_obj.port, verbose, token=agent_obj.access_token)

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

    hostname = tools.format_url(agent_obj.hostname)

    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    client = Operator(hostname, agent_obj.port, verbose, token=agent_obj.access_token)

    client_response = client.architect.get_agent_info()

    if client_response is None:
        logger.error("Contacted agent, but it did not respond.")
        response.update({"agent_info": "Error"})
    else:
        response.update({"agent_info": client_response})

    emit("respond_agent_info", response, json=True, namespace="/system/agent/info")
