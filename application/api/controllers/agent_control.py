import json

from flask import current_app

from application.common import logger, toolbox
from application.models.agent import Agents
from application.workers.game_server_control import startup_game_server
from application.workers.game_server_control import shutdown_game_server
from application.workers.game_server_control import restart_game_server


def startup(request):
    data = request.json
    json_data = json.loads(data)

    try:
        agent_id = json_data["agent_id"]
        game_name = json_data["game_name"]

    except KeyError:
        logger.error("Startup Game Server: Missing Form Input Data")
        return False

    agent_obj = Agents.query.filter_by(agent_id=agent_id).first()

    if agent_obj is None:
        logger.error(f"Startup Game Server: Agent ID {agent_id} does not exist!")
        return False

    hostname = toolbox.format_url_prefix(agent_obj.hostname)
    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    logger.info("Running startup game server command via celery...")

    startup_game_server.apply_async(
        [
            hostname,
            str(agent_obj.port),
            verbose,
            agent_obj.access_token,
            agent_obj.ssl_public_cert,
            game_name,
        ]
    )

    return True


def shutdown(request):
    data = request.json
    json_data = json.loads(data)

    try:
        agent_id = json_data["agent_id"]
        game_name = json_data["game_name"]

    except KeyError:
        logger.error("Shutdown Game Server: Missing Form Input Data")
        return False

    agent_obj = Agents.query.filter_by(agent_id=agent_id).first()

    if agent_obj is None:
        logger.error(f"Shutdown Game Server: Agent ID {agent_id} does not exist!")
        return False

    hostname = toolbox.format_url_prefix(agent_obj.hostname)
    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    logger.info("Shutdown startup game server command via celery...")

    shutdown_game_server.apply_async(
        [
            hostname,
            str(agent_obj.port),
            verbose,
            agent_obj.access_token,
            agent_obj.ssl_public_cert,
            game_name,
        ]
    )

    return True


def restart(request):
    data = request.json
    json_data = json.loads(data)

    try:
        agent_id = json_data["agent_id"]
        game_name = json_data["game_name"]

    except KeyError:
        logger.error("Restart Game Server: Missing Form Input Data")
        return False

    agent_obj = Agents.query.filter_by(agent_id=agent_id).first()

    if agent_obj is None:
        logger.error(f"Restart Game Server: Agent ID {agent_id} does not exist!")
        return False

    hostname = toolbox.format_url_prefix(agent_obj.hostname)
    verbose = current_app.config["OPERATOR_CLIENT_VERBOSE"]

    logger.info("Restart startup game server command via celery...")

    restart_game_server.apply_async(
        [
            hostname,
            str(agent_obj.port),
            verbose,
            agent_obj.access_token,
            agent_obj.ssl_public_cert,
            game_name,
        ]
    )

    return True
