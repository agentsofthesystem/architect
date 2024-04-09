import json

from flask import flash, url_for
from flask_login import current_user

from application.common import logger, toolbox, constants
from application.api.controllers import messages as message_control
from application.extensions import DATABASE
from application.models.agent_group_member import AgentGroupMembers
from application.models.group import Groups
from application.models.group_invite import GroupInvites
from application.models.group_member import GroupMembers
from application.models.user import UserSql


def get_group_by_id(object_id: int, as_obj: bool = False) -> dict:
    group_qry = Groups.query.filter_by(group_id=object_id)
    group_obj = group_qry.first()

    if group_obj is None:
        message = f"Group ID {object_id} does not exist!"
        flash(message)
        return message, 400

    return group_obj if as_obj else group_obj.to_dict()


def get_owned_groups() -> list:
    owned_groups = current_user.groups.all()
    owned_group_list = []

    # TODO - Fix O(N^2) complexity. Works fine for small sizes. This entire chuck of logic would
    # be better built as a series of database table joins.  If the app begins to get slow, then
    # this should be re-worked.
    for group in owned_groups:
        group_dict = group.to_dict()
        group_dict["owner"] = current_user.to_dict()
        group_dict["member_count"] = group.members.count()

        all_members = group.members.all()
        members_list = []

        for member in all_members:
            member_dict = member.to_dict()
            member_id = member_dict["member_id"]
            member_obj = UserSql.query.filter_by(user_id=member_id).first()
            member_dict["user"] = member_obj.to_dict()
            member_dict["user"]["is_friend"] = toolbox.is_friend(current_user.user_id, member_id)
            members_list.append(member_dict)

        invite_objs = GroupInvites.query.filter_by(
            group_id=group.group_id, state=constants.GroupInviteStates.PENDING.value
        ).all()

        invitation_list = []
        group_dict["has_invites"] = True if len(invite_objs) > 0 else False

        for invite in invite_objs:
            invite_dict = invite.to_dict()
            invite_obj = UserSql.query.filter_by(user_id=invite.invite_id).first()
            invite_dict["user"] = invite_obj.to_dict()
            invite_dict["user"]["is_friend"] = toolbox.is_friend(
                current_user.user_id, invite.invite_id
            )
            invitation_list.append(invite_dict)

        group_dict["agent_count"] = AgentGroupMembers.query.filter_by(
            group_member_id=group.group_id
        ).count()
        group_dict["members"] = members_list
        group_dict["invites"] = invitation_list

        owned_group_list.append(group_dict)

    return owned_group_list


def get_associated_groups() -> list:
    member_to_groups = GroupMembers.query.filter_by(member_id=current_user.user_id).all()
    member_to_groups_list = []

    for group in member_to_groups:
        group_id = group.group_id
        group_obj = Groups.query.filter_by(group_id=group_id).first()

        # Don't want to double count owned groups.
        if group_obj.owner_id == current_user.user_id:
            continue

        group_dict = group_obj.to_dict()

        owner_obj = UserSql.query.filter_by(user_id=group_obj.owner_id).first()
        group_dict["owner"] = owner_obj.to_dict()
        group_dict["member_count"] = group_obj.members.count()

        all_members = group_obj.members.all()
        members_list = []
        for member in all_members:
            member_dict = member.to_dict()
            member_id = member_dict["member_id"]
            member_obj = UserSql.query.filter_by(user_id=member_id).first()
            member_dict["user"] = member_obj.to_dict()
            member_dict["user"]["is_friend"] = toolbox.is_friend(current_user.user_id, member_id)
            members_list.append(member_dict)

        group_dict["agent_count"] = AgentGroupMembers.query.filter_by(
            group_member_id=group.group_id
        ).count()
        group_dict["members"] = members_list

        member_to_groups_list.append(group_dict)

    return member_to_groups_list


def create_group(user_id: int, request) -> bool:
    data = request.form

    try:
        name = data["name"]
    except KeyError:
        logger.error("Create Group: Missing Form Input Data")
        flash("Unable to create group because the form was missing data!", "danger")
        return False

    # Name and ownership pair is unique
    exiting_group = Groups.query.filter_by(owner_id=user_id, name=name).first()

    if exiting_group:
        logger.error(f"Create Group: User already has a group named: {name}")
        flash("Unable to create group because it already exists!", "danger")
        return False

    new_group = Groups()
    new_group.active = True
    new_group.name = name
    new_group.owner_id = user_id

    try:
        DATABASE.session.add(new_group)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not create group. Database Error!", "danger")
        return False

    # Now add the user that created the group as a member of the group.
    new_group_member = GroupMembers()
    new_group_member.group_id = new_group.group_id
    new_group_member.member_id = user_id

    try:
        DATABASE.session.add(new_group_member)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not create group membership for self. Database Error!", "danger")
        return False

    return True


def update_group(user_id: int, request) -> bool:
    data = request.form

    try:
        group_id = data["group_id"]
        name = data["name"]
    except KeyError:
        logger.error("Update Group: Missing Form Input Data")
        flash("Unable to update group because the form was missing data!", "danger")
        return False

    group_qry = Groups.query.filter_by(group_id=group_id)
    group_obj = group_qry.first()

    if group_obj is None:
        logger.error("Update Group: Group does not exist")
        flash("Unable to update group because it does not exist!", "danger")
        return False

    update_dict = {"name": name}

    try:
        group_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not update group. Database Error!", "danger")
        return False

    return True


def delete_group(object_id: int) -> bool:
    group_obj = Groups.query.filter_by(group_id=object_id).first()

    if group_obj is None:
        flash("Group does not exist! Cannot delete.", "danger")
        return False

    # If group belongs to any agents, then the user must remove the relationship to the
    # agent(s) first.
    group_memberships = AgentGroupMembers.query.filter_by(group_member_id=group_obj.group_id).all()
    num_memberships = len(group_memberships)

    if num_memberships > 0:
        flash(
            f"Group associated with {num_memberships} Agent(s). Cannot delete until its "
            "removed from all.",
            "warning",
        )
        return False

    group_name = group_obj.name
    group_members = group_obj.members.all()

    try:
        for member in group_members:
            DATABASE.session.delete(member)
    except Exception as error:
        logger.critical(error)
        return False

    group_invites = GroupInvites.query.filter_by(group_id=group_obj.group_id).all()

    try:
        for invite in group_invites:
            DATABASE.session.delete(invite)
    except Exception as error:
        logger.critical(error)
        return False

    # Do one final commit at the end instead of once each loop.
    try:
        DATABASE.session.delete(group_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    flash(f"Group, {group_name}, has been removed.", "info")

    return True


def add_friend_to_group(request) -> bool:
    data = request.form

    try:
        group_id = data["group_id"]
        friends_list = data.getlist("friends_list")
    except KeyError:
        logger.error("Add Friend to Group: Missing Form Input Data")
        flash("Unable to add friend to group because the form was missing data!", "danger")
        return False

    users_added = 0

    # Get group name
    group_obj = Groups.query.filter_by(group_id=group_id).first()

    if group_obj is None:
        flash(f"Error: Group ID {group_id} does not exist... something is wrong!")
        return False

    group_name = group_obj.name
    subject = "Added to Group!"
    group_href = url_for("protected.system_groups", _external=True)
    message = (
        f"<p>You have been added to group, {group_name}, by the group owner. Go to the "
        f'<a href="{group_href}">Groups Page</a> to and have a look..</p>'
    )

    for user_id in friends_list:
        # Make sure friend isn't already in the group.
        member_obj = GroupMembers.query.filter_by(group_id=group_id, member_id=user_id).first()

        if member_obj:
            user_obj = UserSql.query.filter_by(user_id=user_id).first()
            flash(
                f"The person, {user_obj.username}, is already in the group. Skipping...", "warning"
            )
            continue

        new_group_member = GroupMembers()
        new_group_member.group_id = group_id
        new_group_member.member_id = user_id
        DATABASE.session.add(new_group_member)
        users_added += 1

        message_control.create_direct_message(
            group_obj.owner_id,
            user_id,
            message,
            subject,
            category=constants.MessageCategories.SOCIAL,
        )

    if users_added > 0:
        try:
            DATABASE.session.commit()
        except Exception as error:
            logger.critical(error)
            return False

        flash("Successfully added friend(s) to group!", "info")
    else:
        flash("No new users added to the group.", "warning")

    return True


def invite_friend_to_group(request) -> bool:
    data = request.form

    try:
        group_id = data["group_id"]
        requestor_id = data["requestor_id"]
        friends_list = data.getlist("friends_list")
    except KeyError:
        logger.error("Invite Friend to Group: Missing Form Input Data")
        flash("Unable to invite friend to group because the form was missing data!", "danger")
        return False

    if len(friends_list) > 1:
        flash("Error: Can only invite one user at a time.", "danger")
        return False

    invited_user_id = int(friends_list[0])

    group_qry = Groups.query.filter_by(group_id=group_id)
    group_obj = group_qry.first()

    if group_obj is None:
        flash("Error: Group does not exist!", "danger")
        return False

    # The invited user ID can't be the group owner. Can't invite the group owner to their own group!
    if invited_user_id == group_obj.owner_id:
        flash("Error: Cannot invite the group owner to their own group! Try again.", "warning")
        return False

    # Cannot invite the user to the group, if the user is already in the group!
    group_member_obj = GroupMembers.query.filter_by(
        group_id=group_obj.group_id, member_id=invited_user_id
    ).first()

    if group_member_obj:
        invited_user_obj = UserSql.query.filter_by(user_id=invited_user_id).first()
        flash(
            f"Warning: {invited_user_obj.username} is already in the group. "
            "No need to invite them again!",
            "warning",
        )
        return False

    # Also, don't allow duplicate invites...
    existing_group_invite_obj = GroupInvites.query.filter_by(
        group_id=group_obj.group_id,
        invite_id=invited_user_id,
        requestor_id=requestor_id,
        state=constants.GroupInviteStates.PENDING.value,
    ).first()

    if existing_group_invite_obj:
        invited_user_obj = UserSql.query.filter_by(user_id=invited_user_id).first()
        flash(
            f"Warning: An invite for user, {invited_user_obj.username} is already pending.",
            "warning",
        )
        return False

    # Defaults to pending state initially so do not have to set that.
    new_group_invite = GroupInvites()
    new_group_invite.group_id = group_id
    new_group_invite.requestor_id = requestor_id
    new_group_invite.invite_id = invited_user_id

    try:
        DATABASE.session.add(new_group_invite)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    requestor_obj = UserSql.query.filter_by(user_id=requestor_id).first()
    owner_obj = UserSql.query.filter_by(user_id=group_obj.owner_id).first()
    invited_obj = UserSql.query.filter_by(user_id=invited_user_id).first()

    # DM the group owner.
    subject = f"Request to add user to group, {group_obj.name}."
    group_href = url_for("protected.system_groups", _external=True)
    message = (
        f"<p>Hey, {owner_obj.username}! {requestor_obj.username} is requesting that you "
        f"add user, {invited_obj.username}, to your group, {group_obj.name}. Go to the "
        f'<a href="{group_href}">Groups Page</a> to and have a look..</p>'
    )

    message_control.create_direct_message(
        requestor_id,
        group_obj.owner_id,
        message,
        subject,
        category=constants.MessageCategories.SOCIAL,
    )

    flash("The owner of the group will Approve/Reject the invite.", "info")

    return True


def remove_user_from_group(group_id: int, member_id: int) -> bool:
    group_member_obj = GroupMembers.query.filter_by(group_id=group_id, member_id=member_id).first()

    if group_member_obj is None:
        flash(
            "Error: Unable to remove friend from group, because user was not a part of group!",
            "danger",
        )
        return False

    try:
        DATABASE.session.delete(group_member_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    group_obj = Groups.query.filter_by(group_id=group_id).first()

    # DM the user removed from the group.
    subject = f"Removed from group, {group_obj.name}."
    message = f"<p>You have been removed from the group, {group_obj.name}. </p>"

    message_control.create_direct_message(
        group_obj.owner_id, member_id, message, subject, category=constants.MessageCategories.SOCIAL
    )

    flash("User was removed from group.", "info")

    return True


def transfer_group(request) -> bool:
    data = request.form

    try:
        group_id = data["group_id"]
        friends_list = data.getlist("friends_list")
    except KeyError:
        logger.error("Add Friend to Group: Missing Form Input Data")
        flash("Unable to add friend to group because the form was missing data!", "danger")
        return False

    if len(friends_list) > 1:
        flash("Error: Can only transfer to one user.", "danger")
        return False

    group_qry = Groups.query.filter_by(group_id=group_id)
    group_obj = group_qry.first()

    if group_obj is None:
        flash("Error: Group does not exist!", "danger")
        return False

    old_owner_id = group_obj.owner_id
    group_name = group_obj.name
    new_owner_id = friends_list[0]

    update_dict = {"owner_id": new_owner_id}

    try:
        group_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    old_owner_obj = UserSql.query.filter_by(user_id=old_owner_id).first()

    subject = "Group Transferred to you."
    friend_href = url_for("protected.system_groups", _external=True)
    message = (
        f"<p>Hey, {current_user.username}! {old_owner_obj.username} has transferred ownership "
        f"of group, {group_name}, to you. Go to the "
        f'<a href="{friend_href}">Groups Page</a> to and have a look..</p>'
    )

    message_control.create_direct_message(
        old_owner_id, new_owner_id, message, subject, category=constants.MessageCategories.SOCIAL
    )

    flash(f"Group, {group_name}, successfully transferred.", "info")

    return True


def remove_deleted_friend_from_owned_groups(deleted_friend_user_id: int):
    # See if current user owns any groups.
    owned_groups = get_owned_groups()

    deleted_group_memberships = 0

    # If there are any...
    for group in owned_groups:
        # check if the friend is any of these groups.
        group_member_obj = None
        group_id = group["group_id"]
        owner_id = group["owner_id"]

        # If the deleted friend is not the group owner, delete the membership of the user that
        # was deleted as a friend..
        if deleted_friend_user_id != owner_id:
            group_member_obj = GroupMembers.query.filter_by(
                group_id=group_id, member_id=deleted_friend_user_id
            ).first()
        else:
            # Otherwise, delete the current user.
            group_member_obj = GroupMembers.query.filter_by(
                group_id=group_id, member_id=current_user.user_id
            ).first()

        if group_member_obj:
            DATABASE.session.delete(group_member_obj)
            deleted_group_memberships += 1

    if deleted_group_memberships > 0:
        try:
            DATABASE.session.commit()
        except Exception as error:
            logger.critical(error)
            flash("Could not remove friend from owned groups. Database Error!", "danger")
            raise Exception("Database Error")


def resolve_group_invitation(request) -> bool:
    data = request.json

    json_data = json.loads(data)

    try:
        group_id = json_data["group_id"]
        invite_id = json_data["invite_id"]
        requestor_id = json_data["requestor_id"]
        action = json_data["action"]
    except KeyError:
        logger.error("Invite Friend to Group: Missing Form Input Data")
        flash("Unable to resolve invitation to group because the form was missing data!", "danger")
        return False

    # Make sure group exists, first.
    group_obj = Groups.query.filter_by(group_id=group_id).first()

    # Get invited user object
    invited_user_obj = UserSql.query.filter_by(user_id=invite_id).first()

    if group_obj is None:
        flash("Error: Group does not exist!", "danger")
        return False

    invitation_qry = GroupInvites.query.filter_by(
        group_id=group_id,
        invite_id=invite_id,
        requestor_id=requestor_id,
        state=constants.GroupInviteStates.PENDING.value,
    )
    invitation_obj = invitation_qry.first()

    if invitation_obj is None:
        flash("Error: The invitation object does not exist.", "danger")
        return False

    if action.lower() == "accept":
        update_dict = {"state": constants.GroupInviteStates.ACCEPTED.value}

        new_group_member = GroupMembers()
        new_group_member.group_id = group_id
        new_group_member.member_id = invite_id
        DATABASE.session.add(new_group_member)

        flash_message = f"The user, {invited_user_obj.username}, was admitted to the group."
        flash_message_type = "info"

        # DM The user that was added.
        subject = f"You have been added to group, {group_obj.name}."
        group_href = url_for("protected.system_groups", _external=True)
        message = (
            f"<p>Hey, {invited_user_obj.username}! You have been admitted to group, "
            f"{group_obj.name}, by the group owner. Go to the "
            f'<a href="{group_href}">Groups Page</a> to and have a look...</p>'
        )

        message_control.create_direct_message(
            group_obj.owner_id,
            invite_id,
            message,
            subject,
            category=constants.MessageCategories.SOCIAL,
        )

    else:
        update_dict = {"state": constants.GroupInviteStates.REJECTED.value}
        flash_message = f"The user, {invited_user_obj.username}, was not admitted to the group."
        flash_message_type = "warning"

        # DM The user that made the request to let that person know the invite was rejected.
        subject = "User Invite Rejected"
        message = (
            f"The group owner has decided not to admit user, {invited_user_obj.username}, "
            f"to the group, {group_obj.name}"
        )
        message_control.create_direct_message(
            group_obj.owner_id,
            requestor_id,
            message,
            subject,
            category=constants.MessageCategories.SOCIAL,
        )

    invitation_qry.update(update_dict)

    try:
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    flash(flash_message, flash_message_type)

    return True
