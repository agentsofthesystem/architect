from flask import flash, url_for
from flask_login import current_user

from application.common import logger
from application.api.controllers.messages import create_direct_message
from application.extensions import DATABASE
from application.models.group import Groups
from application.models.group_member import GroupMembers
from application.models.user import UserSql


def get_group_by_id(object_id: int) -> dict:
    group_obj = Groups.query.filter_by(group_id=object_id).first()

    if group_obj is None:
        message = f"Group ID {object_id} does not exist!"
        flash(message)
        return message, 400

    return group_obj.to_dict()


def get_owned_groups() -> list:
    owned_groups = current_user.groups.all()
    owned_group_list = []

    # TODO - Fix O(N^2) complexity. Works fine for small sizes. Works for now..
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
            members_list.append(member_dict)

        # TODO - Add agents this group has access too
        group_dict["agent_count"] = 0
        group_dict["agents"] = []
        group_dict["members"] = members_list

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
            members_list.append(member_dict)

        # TODO - Add agents this group has access too
        group_dict["agent_count"] = 0
        group_dict["agents"] = []
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

    group_name = group_obj.name
    group_members = group_obj.members.all()

    try:
        for member in group_members:
            DATABASE.session.delete(member)
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


def remove_friend_from_group(group_id: int, member_id: int) -> bool:
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

    # TODO - Send Message/Email to tell user that they were removed from the group.

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
    friend_href = url_for("protected.system_groups")
    message = (
        f"<p>Hey, {current_user.first_name}! {old_owner_obj.username} has transferred ownership "
        f"of group, {group_name}, to you. Go to the "
        f'<a href="{friend_href}">Groups Page</a> to and have a look..</p>'
    )

    create_direct_message(old_owner_id, new_owner_id, message, subject)

    flash(f"Group, {group_name}, successfully transferred.", "info")

    return True


def remove_deleted_friend_from_groups(deleted_friend_user_id: int):
    # See if current user owns any groups.
    owned_groups = get_owned_groups()
    member_to_groups = get_associated_groups()

    all_groups = owned_groups + member_to_groups

    deleted_group_memberships = 0

    # If there are any...
    for group in all_groups:
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
