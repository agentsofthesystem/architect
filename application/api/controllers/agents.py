from flask import flash, url_for
from flask_login import current_user

from application.api.controllers import friends as friend_control
from application.api.controllers import groups as group_control
from application.api.controllers import messages as message_control
from application.api.controllers import users as user_control
from application.common import constants, logger
from application.common.exceptions import InvalidUsage
from application.extensions import DATABASE
from application.models.agent import Agents
from application.models.agent_group_member import AgentGroupMembers
from application.models.agent_friend_member import AgentFriendMembers
from application.models.monitor import Monitor


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

    for item in agent_items:
        owner_id = item["owner_id"]
        owner_obj = user_control.get_user_by_id(owner_id)
        agent_share_limit = (
            constants.DEFAULT_USERS_PER_AGENT_FREE
            if not owner_obj.subscribed
            else constants.DEFAULT_USERS_PER_AGENT_PAID
        )
        agent_obj = Agents.query.filter_by(agent_id=item["agent_id"]).first()
        item["agent_share_limit"] = agent_share_limit
        item["num_users"] = agent_obj.num_users
        item["num_groups"] = agent_obj.groups_with_access.count()

    return agent_items


def get_associated_agents() -> dict:
    # Get groups, that user belongs to.
    associated_groups = group_control.get_associated_groups()

    # Build agent id list from groups
    combined_agent_list = []

    for group in associated_groups:
        membership_objs = AgentGroupMembers.query.filter_by(group_member_id=group["group_id"]).all()
        for membership in membership_objs:
            agent_id = membership.agent_id
            this_agent_obj = Agents.query.filter_by(agent_id=agent_id).first()
            is_own_agent = this_agent_obj.owner_id == current_user.user_id
            if agent_id not in combined_agent_list and not is_own_agent:
                combined_agent_list.append(membership.agent_id)

    # Check on direct agents from friends. Build list first, get the agents owned by friends,
    # and finally check for agent relationships.
    friend_id_list = []
    friends_list = friend_control.get_my_friends()

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
            this_agent_obj = Agents.query.filter_by(agent_id=agent_id).first()
            is_own_agent = this_agent_obj.owner_id == current_user.user_id
            if agent_id not in combined_agent_list and not is_own_agent:
                combined_agent_list.append(membership.agent_id)

    # Get all agents with ids matching the list.
    agent_qry = Agents.query.filter(Agents.agent_id.in_(combined_agent_list))

    agents_dict = Agents.to_collection_dict(
        agent_qry, constants.DEFAULT_PAGE, constants.DEFAULT_PER_PAGE_MAX, "", ignore_links=True
    )

    agent_items = agents_dict["items"]

    # Pack in the user information.
    for agent in agent_items:
        agents_obj = get_agent_by_id(agent["agent_id"], as_obj=True)
        owner_id = agent["owner_id"]
        owner_obj = user_control.get_user_by_id(owner_id)
        agent["owner"] = owner_obj.to_dict()
        agent_share_limit = (
            constants.DEFAULT_USERS_PER_AGENT_FREE
            if not owner_obj.subscribed
            else constants.DEFAULT_USERS_PER_AGENT_PAID
        )
        agent_obj = Agents.query.filter_by(agent_id=agent["agent_id"]).first()
        agent["agent_share_limit"] = agent_share_limit
        agent["num_users"] = agents_obj.num_users
        agent["num_groups"] = agent_obj.groups_with_access.count()

    return agent_items


def create_agent(request) -> bool:
    data = request.form

    try:
        name = data["name"]
        hostname = data["hostname"]
        port = data["port"]
        owner_id = data["owner_id"]
        access_token = data["access_token"]
        ssl_public_cert = data["ssl_public_cert"]

    except KeyError:
        logger.error("Create Agent: Missing Form Input Data")
        flash("There was an internal error...", "danger")
        return False

    if "http://" in hostname:
        flash("Warning: You must use https:// or just enter the domain name only.", "warning")
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
    new_agent.ssl_public_cert = ssl_public_cert

    try:
        DATABASE.session.add(new_agent)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could Create new Agent. Database Error!", "danger")
        return False

    # At minimum, create an agent health monitor.
    agent_health_monitor = Monitor()
    agent_health_monitor.agent_id = new_agent.agent_id
    agent_health_monitor.monitor_type = constants.monitor_type_to_string(
        constants.MonitorTypes.AGENT
    )
    agent_health_monitor.has_fault = False
    agent_health_monitor.active = False

    try:
        DATABASE.session.add(agent_health_monitor)
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
        ssl_public_cert = data["ssl_public_cert"]

    except KeyError:
        logger.error("Create Agent: Missing Form Input Data")
        flash("There was an internal error...", "danger")
        return False

    if "http://" in hostname:
        flash("Warning: You must use https:// or just enter the domain name only.", "warning")
        return False

    agent_qry = Agents.query.filter_by(agent_id=agent_id)

    if agent_qry.first() is None:
        raise InvalidUsage("Error: Update Agent Does not exist!", status_code=400)

    update_dict = {
        "name": name,
        "hostname": hostname,
        "port": port,
        "access_token": access_token,
        "ssl_public_cert": ssl_public_cert,
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
    """
    Remove an agent from database along with all relationships.

    Args:
        object_id: Agent ID to delete.
    """
    agent_qry = Agents.query.filter_by(agent_id=object_id)

    agent_obj = agent_qry.first()

    if agent_obj is None:
        raise InvalidUsage(
            "Unable to Delete Agent ID # {object_id}. Does Not Exist!", status_code=400
        )

    logger.debug(f"Deactivating Agent: {agent_obj.name}")
    agent_groups = agent_obj.groups_with_access.all()
    agent_friends = agent_obj.friends_with_access.all()
    attached_monitors = agent_obj.attached_monitors.all()

    try:
        # Delete monitor faults and attributes.
        for monitor in attached_monitors:
            mfaults = monitor.monitor_faults.all()
            mattrs = monitor.monitor_attributes.all()
            for fault in mfaults:
                DATABASE.session.delete(fault)
            for mattribute in mattrs:
                DATABASE.session.delete(mattribute)

        # Delete monitor itself
        for monitor in attached_monitors:
            DATABASE.session.delete(monitor)

        # Delete group relationships
        for group in agent_groups:
            DATABASE.session.delete(group)

        # Delete friend relationships
        for friend in agent_friends:
            DATABASE.session.delete(friend)

        DATABASE.session.delete(agent_obj)  # Agent
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not Remove Agent. Database Error!", "danger")
        DATABASE.session.rollback()
        return False

    return True


def reactivate_agent(object_id: int) -> bool:
    """
    Set the agent active flag to True.

    Args:
        object_id: Agent ID to delete.
    """
    agent_qry = Agents.query.filter_by(agent_id=object_id)

    agent_obj = agent_qry.first()

    if agent_obj is None:
        raise InvalidUsage(
            "Unable to Delete Agent ID # {object_id}. Does Not Exist!", status_code=400
        )

    update_dict = {"active": True}
    try:
        agent_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not Reactivate Agent. Database Error!", "danger")
        DATABASE.session.rollback()
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

    # Make sure the agent is not already shared with a different group.
    agent_obj = get_agent_by_id(agent_id, as_obj=True)
    group_obj = group_control.get_group_by_id(group_id, as_obj=True)
    agent_owner_id = agent_obj.owner_id
    num_groups = agent_obj.groups_with_access.count()
    group_members = group_obj.members.all()

    # Get the group id member list, but remove the owner id.
    group_members_ids = [member.member_id for member in group_members]
    group_members_ids.remove(group_obj.owner_id)

    if num_groups > 0:
        flash("Error: This agent is already shared with a group.", "danger")
        return False

    # Make sure its not already shared... This an an extra check to be on safe side.
    share_obj = AgentGroupMembers.query.filter_by(
        agent_id=agent_id, group_member_id=group_id
    ).first()

    if share_obj:
        flash("Error: This group has already been shared to this Agent.", "danger")
        return False

    # Before creating the group membership, check if the the number of people in the group
    # will exceed the share limit.
    owner_obj = user_control.get_user_by_id(agent_owner_id)
    agent_unique_user_id_list = agent_obj.get_users(as_list=True)
    agent_share_limit = (
        constants.DEFAULT_USERS_PER_AGENT_FREE
        if not owner_obj.subscribed
        else constants.DEFAULT_USERS_PER_AGENT_PAID
    )

    # Eliminate duplicates with exclusive or.
    exclusive_list = list(set(group_members_ids) ^ set(agent_unique_user_id_list))

    if len(exclusive_list) > agent_share_limit:
        flash("Error: Adding this group will put the agent over the share limit.", "danger")
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

    subject = "Agent Shared via Group"
    agent_href = url_for("protected.system_agent_info", agent_id=agent_id, _external=True)
    message = (
        f"<p>Access granted to Agent: {agent_obj.name}.</p>"
        f"<p>You has access to this agent because you belong to group, {group_obj.name}.</p>"
        f'<p>Go to the <a href="{agent_href}">Agent Info Page</a> to and have a look...</p>'
    )

    for member in group_members:
        # Technically, the owning user is also a member of the group. Skip because do not
        # need to send message to self.
        if member.member_id == current_user.user_id:
            continue

        message_control.create_direct_message(
            current_user.user_id,
            member.member_id,
            message,
            subject,
            category=constants.MessageCategories.SOCIAL,
        )

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

    agent_obj = get_agent_by_id(agent_id, as_obj=True)
    agent_owner_id = agent_obj.owner_id

    # Check whether or not the friend is already a member of the agent.
    share_obj = AgentFriendMembers.query.filter_by(
        agent_id=agent_id, friend_member_id=friend_user_id
    ).first()

    if share_obj:
        flash("Error: This Friend has already been shared to this Agent.", "danger")
        return False

    # Check whether or not adding the friend will put the agent over the share budget/limit.
    owner_obj = user_control.get_user_by_id(agent_owner_id)
    num_users = agent_obj.num_users
    agent_share_limit = (
        constants.DEFAULT_USERS_PER_AGENT_FREE
        if not owner_obj.subscribed
        else constants.DEFAULT_USERS_PER_AGENT_PAID
    )

    if num_users + 1 > agent_share_limit:
        flash("Error: Adding this friend will put the agent over the share limit.", "danger")
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

    subject = "Agent Shared via Friendship"
    agent_href = url_for("protected.system_agent_info", agent_id=agent_id, _external=True)
    message = (
        f"<p>Access granted to Agent, {agent_obj.name}.</p>"
        "<p>You will have access to this agent regardless of belonging "
        "to a group which also has access.</p>"
        f'<p>Go to the <a href="{agent_href}">Agent Info Page</a> to and have a look..</p>'
    )

    message_control.create_direct_message(
        current_user.user_id,
        friend_user_id,
        message,
        subject,
        category=constants.MessageCategories.SOCIAL,
    )

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

    agent_id = membership_obj.agent_id
    group_id = membership_obj.group_member_id

    try:
        DATABASE.session.delete(membership_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not remove group from agent. Database Error!", "danger")
        return False

    agent_obj = get_agent_by_id(agent_id=agent_id, as_obj=True)
    group_obj = group_control.get_group_by_id(group_id, as_obj=True)
    group_members = group_obj.members.all()

    subject = "Group access to Agent revoked."
    message = (
        f"<p>Access Revoked from Agent: {agent_obj.name}.</p>"
        f"<p>The group, {group_obj.name}, no longer has access to the agent.</p>"
        f"<p>That means you no longer have access to this agent unless you have direct access "
        "granted via friendship</p>"
    )

    for member in group_members:
        # Technically, the owning user is also a member of the group. Skip because do not
        # need to send message to self.
        if member.member_id == current_user.user_id:
            continue

        message_control.create_direct_message(
            current_user.user_id,
            member.member_id,
            message,
            subject,
            category=constants.MessageCategories.SOCIAL,
        )

    flash("Group Membership Removed From Agent!", "info")

    return True


def remove_friend_membership(membership_id: int) -> bool:
    membership_obj = AgentFriendMembers.query.filter_by(
        agent_friend_member_id=membership_id
    ).first()

    if membership_obj is None:
        flash("Error: Unable to remove friend from agent because it doesn't exist!", "danger")
        return False

    friend_member_id = membership_obj.friend_member_id

    try:
        DATABASE.session.delete(membership_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not remove friend from agent. Database Error!", "danger")
        return False

    agent_obj = get_agent_by_id(membership_obj.agent_id, as_obj=True)

    subject = "Agent Access Revoked"
    message = (
        f"<p>Access revoked for Agent, {agent_obj.name}.</p>"
        "<p>You may still have access to this agent if you belong to a group with access.</p>"
        "<p>However, if you only had access via friendship then you will not.</p>"
    )

    message_control.create_direct_message(
        current_user.user_id,
        friend_member_id,
        message,
        subject,
        category=constants.MessageCategories.SOCIAL,
    )

    flash("Friend Removed From Agent!", "info")

    return True
