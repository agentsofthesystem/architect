from flask import flash
from flask_login import current_user

from application.api.controllers import friends
from application.api.controllers import groups
from application.api.controllers import users
from application.common import constants, logger, tools
from application.common.exceptions import InvalidUsage
from application.extensions import DATABASE
from application.models.agent import Agents
from application.models.agent_group_member import AgentGroupMembers
from application.models.agent_friend_member import AgentFriendMembers

from operator_client import Operator


def get_agent_by_id(agent_id: int, as_obj: bool = False) -> dict:
    agent_qry = Agents.query.filter_by(agent_id=agent_id)

    agent_dict = Agents.to_collection_dict(
        agent_qry, constants.DEFAULT_PAGE, constants.DEFAULT_PER_PAGE_MAX, "", ignore_links=True
    )

    return agent_qry.first() if as_obj else agent_dict["items"]


def get_agents_by_owner(owner_id: int) -> []:
    owner_agents_qry = Agents.query.filter_by(owner_id=owner_id)

    owner_agents = Agents.to_collection_dict(
        owner_agents_qry,
        constants.DEFAULT_PAGE,
        constants.DEFAULT_PER_PAGE_MAX,
        "",
        ignore_links=True,
    )

    agent_items = owner_agents["items"]

    return agent_items


def get_associated_agents() -> dict:
    # Get groups, that user belongs to.
    associated_groups = groups.get_associated_groups()

    # Build agent id list from groups
    combined_agent_list = []

    for group in associated_groups:
        membership_objs = AgentGroupMembers.query.filter_by(group_member_id=group["group_id"]).all()
        for membership in membership_objs:
            agent_id = membership.agent_id
            if agent_id not in combined_agent_list:
                combined_agent_list.append(membership.agent_id)

    # Check on direct agents from friends. Build list first, get the agents owned by friends,
    # and finally check for agent relationships.
    friend_id_list = []
    friends_list = friends.get_my_friends()

    for friend in friends_list:
        if current_user.user_id == friend["initiator_id"]:
            friend_id_list.append(friend["receiver_id"])
        else:
            friend_id_list.append(friend["initiator_id"])

    # Get IDs of agent belonging to each friend.
    agents_owned_by_friends = Agents.query.filter(Agents.owner_id.in_(friend_id_list)).all()

    # Finally see if you have any relationship to share any agent owned by any of your friends.
    for agent in agents_owned_by_friends:
        # In this case, the friend member id is the current user.
        membership_objs = AgentFriendMembers.query.filter_by(
            agent_id=agent.agent_id, friend_member_id=current_user.user_id
        ).all()
        for membership in membership_objs:
            agent_id = membership.agent_id
            if agent_id not in combined_agent_list:
                combined_agent_list.append(membership.agent_id)

    # Get all agents with ids matching the list.
    agent_qry = Agents.query.filter(Agents.agent_id.in_(combined_agent_list))

    agents_obj = Agents.to_collection_dict(
        agent_qry, constants.DEFAULT_PAGE, constants.DEFAULT_PER_PAGE_MAX, "", ignore_links=True
    )

    agent_items = agents_obj["items"]

    # Pack in the user information.
    for agent in agent_items:
        owner_id = agent["owner_id"]
        owner_obj = users.get_user_by_id(owner_id)
        agent["owner"] = owner_obj.to_dict()

    return agent_items


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
        flash("Could Create new Agent. Database Error!", "danger")
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
        flash("Could not update Agent. Database Error!", "danger")
        return False

    return True


def deactivate_agent(object_id: int) -> bool:
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
        flash("Could not Remove Agent. Database Error!", "danger")
        return False

    return True


def share_agent_with_group(request) -> bool:
    data = request.form

    try:
        agent_id = data["agent_id"]
        group_list = data.getlist("group_list")
    except KeyError:
        logger.error("Share Agent with Group: Missing Form Input Data")
        flash("Unable to share group with agent because the form was missing data!", "danger")
        return False

    # This should never happen but just in case..
    if len(group_list) > 1:
        flash("Error: For some reason there was more than 1 group in form submission.", "danger")
        return False

    group_id = group_list[0]

    # Make sure its not already shared...
    share_obj = AgentGroupMembers.query.filter_by(
        agent_id=agent_id, group_member_id=group_id
    ).first()

    if share_obj:
        flash("Error: This group has already been shared to this Agent.", "danger")
        return False

    new_group_member = AgentGroupMembers()
    new_group_member.agent_id = agent_id
    new_group_member.group_member_id = group_id

    try:
        DATABASE.session.add(new_group_member)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not Share Agent To Group. Database Error!", "danger")
        return False

    # TODO - Send message to users in group that they were added to an agent.

    flash("Successfully shared Agent with Group!", "info")

    return True


def share_agent_with_friend(request) -> bool:
    data = request.form

    try:
        agent_id = data["agent_id"]
        friend_list = data.getlist("friends_list")
    except KeyError:
        logger.error("Share Agent with Friend: Missing Form Input Data")
        flash("Unable to share agent with friend because the form was missing data!", "danger")
        return False

    # This should never happen but just in case..
    if len(friend_list) > 1:
        flash("Error: For some reason there was more than 1 friend in form submission.", "danger")
        return False

    friend_user_id = friend_list[0]

    share_obj = AgentFriendMembers.query.filter_by(
        agent_id=agent_id, friend_member_id=friend_user_id
    ).first()

    if share_obj:
        flash("Error: This Friend has already been shared to this Agent.", "danger")
        return False

    new_friend_member = AgentFriendMembers()
    new_friend_member.agent_id = agent_id
    new_friend_member.friend_member_id = friend_user_id

    try:
        DATABASE.session.add(new_friend_member)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not Share Agent With Friend. Database Error!", "danger")
        return False

    flash("Successfully shared Agent with Friend!", "info")

    return True


def remove_deleted_friend_from_agents(agent_owner_id: int, deleted_friend_user_id: int):
    # Get all agents belonging to the owner.
    agent_objs = Agents.query.filter_by(owner_id=agent_owner_id).all()

    # Get all relationships between
    for agent in agent_objs:
        # There can only ever be one so use .first() instead of .all()
        agent_friend_membership = AgentFriendMembers.query.filter_by(
            agent_id=agent.agent_id, friend_member_id=deleted_friend_user_id
        ).first()
        if agent_friend_membership:
            DATABASE.session.delete(agent_friend_membership)

    # Commit once. Save the number of transactions.
    try:
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not eliminate Friend from all my agents. Database Error!", "danger")


def remove_group_membership(membership_id: int) -> bool:
    membership_obj = AgentGroupMembers.query.filter_by(agent_group_member_id=membership_id).first()

    if membership_obj is None:
        flash("Error: Unable to remove group from agent because it doesn't exist!", "danger")
        return False

    try:
        DATABASE.session.delete(membership_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not remove group from agent. Database Error!", "danger")
        return False

    flash("Group Member Removed From Agent!", "info")

    return True


def remove_friend_membership(membership_id: int) -> bool:
    membership_obj = AgentFriendMembers.query.filter_by(
        agent_friend_member_id=membership_id
    ).first()

    if membership_obj is None:
        flash("Error: Unable to remove friend from agent because it doesn't exist!", "danger")
        return False

    try:
        DATABASE.session.delete(membership_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not remove friend from agent. Database Error!", "danger")
        return False

    # TODO - Message user that their access to the agent has been removed.

    flash("Friend Removed From Agent!", "info")

    return True


def get_agent_info(hostname: str, port: str, token: str, agent_id: int) -> dict:
    hostname = tools.format_url(hostname)

    client = Operator(hostname, port, token=token)

    return client.architect.get_agent_info(agent_id)
