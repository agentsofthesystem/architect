from flask import flash

from application.common import constants, logger
from application.common.exceptions import InvalidUsage
from application.extensions import DATABASE
from application.models.agent import Agents


def get_agent_by_id(agent_id: int) -> {}:
    agent_qry = Agents.query.filter_by(agent_id=agent_id)

    agent_obj = Agents.to_collection_dict(
        agent_qry, constants.DEFAULT_PAGE, constants.DEFAULT_PER_PAGE_MAX, "", ignore_links=True
    )

    return agent_obj["items"]


def get_agents_by_owner(owner_id: int) -> []:
    owner_agents_qry = Agents.query.filter_by(owner_id=owner_id)

    owner_agents = Agents.to_collection_dict(
        owner_agents_qry,
        constants.DEFAULT_PAGE,
        constants.DEFAULT_PER_PAGE_MAX,
        "",
        ignore_links=True,
    )

    return owner_agents["items"]


def create_agent(request) -> bool:
    data = request.form

    try:
        name = data["name"]
        hostname = data["hostname"]
        port = data["port"]
        owner_id = data["owner_id"]
        access_token = data["access_token"]

    except KeyError:
        logger.error("Create Agent: Missing Form Input Data")
        flash("There was an internal error...", "danger")
        return False

    # Owner ID prevents two accounts from adding the same agent.
    check_agent_obj = Agents.query.filter_by(
        hostname=hostname, port=port, owner_id=owner_id
    ).first()

    if check_agent_obj:
        flash("An Agent with Same Hostname & Port Already Exists!", "danger")
        return False

    new_agent = Agents()
    new_agent.name = name
    new_agent.hostname = hostname
    new_agent.port = port
    new_agent.owner_id = owner_id
    new_agent.access_token = access_token

    try:
        DATABASE.session.add(new_agent)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    return True


def update_agent(request):
    data = request.form

    try:
        name = data["name"]
        hostname = data["hostname"]
        port = data["port"]
        agent_id = data["agent_id"]
        access_token = data["access_token"]

    except KeyError:
        logger.error("Create Agent: Missing Form Input Data")
        flash("There was an internal error...", "danger")
        return False

    agent_qry = Agents.query.filter_by(agent_id=agent_id)

    if agent_qry.first() is None:
        raise InvalidUsage("Error: Update Agent Does not exist!", status_code=400)

    update_dict = {
        "name": name,
        "hostname": hostname,
        "port": port,
        "access_token": access_token,
    }

    try:
        agent_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    return True


def deactivate_agent(object_id: int):
    # TODO - When deleting an agent, may want to later just mark active=False, and will also
    # have to handle friend/group relationships.
    agent_qry = Agents.query.filter_by(agent_id=object_id)

    agent_obj = agent_qry.first()

    if agent_obj is None:
        raise InvalidUsage(
            "Unable to Delete Agent ID # {object_id}. Does Not Exist!", status_code=400
        )

    try:
        DATABASE.session.delete(agent_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    return True
