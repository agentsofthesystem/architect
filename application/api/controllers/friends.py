import json
import uuid

from flask import flash, url_for
from flask_login import current_user

from application.common import logger
from application.common.constants import FriendRequestStates
from application.api.controllers import groups as group_control
from application.api.controllers import messages as message_control
from application.extensions import DATABASE
from application.models.friend import Friends
from application.models.friend_request import FriendRequests
from application.models.user import UserSql


def generate_friend_code(email: str):
    return uuid.uuid5(uuid.NAMESPACE_DNS, email)


def add_friend_code_to_user(user_id: int, friend_code: str):
    user_qry = UserSql.query.filter_by(user_id=user_id)
    update_dict = {"friend_code": friend_code}

    try:
        user_qry.update(update_dict)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    return True


def get_my_friend_requests() -> list:
    incoming = current_user.incoming_friend_requests.filter_by(
        state=FriendRequestStates.PENDING.value
    ).all()
    outgoing = current_user.outgoing_friend_requests.filter_by(
        state=FriendRequestStates.PENDING.value
    ).all()

    final_list = []

    for fr in incoming:
        fr_dict = fr.to_dict()
        sender = UserSql.query.filter_by(user_id=fr_dict["sender_id"]).first()
        fr_dict["request_type"] = "Incoming"
        fr_dict["sender"] = sender.to_dict()
        final_list.append(fr_dict)

    for fr in outgoing:
        fr_dict = fr.to_dict()
        recipient = UserSql.query.filter_by(user_id=fr_dict["recipient_id"]).first()
        fr_dict["request_type"] = "Outgoing"
        fr_dict["recipient"] = recipient.to_dict()
        final_list.append(fr_dict)

    return final_list


def get_my_friends() -> list:
    final_list = []

    if current_user is None:
        logger.error("Friends:get_my_friend - Current User is NoneType")
        return final_list

    initiated_friends = current_user.initiated_friends.all()
    received_friends = current_user.received_friends.all()

    all_friends = initiated_friends + received_friends

    for friend in all_friends:
        friend_dict = friend.to_dict()
        receiver = UserSql.query.filter_by(user_id=friend_dict["receiver_id"]).first()
        initiator = UserSql.query.filter_by(user_id=friend_dict["initiator_id"]).first()
        friend_dict["receiver"] = receiver.to_dict()
        friend_dict["initiator"] = initiator.to_dict()
        final_list.append(friend_dict)

    return final_list


def create_new_friend_request(request) -> bool:
    data = request.form

    try:
        friend_code = data["friend_code"]

    except KeyError:
        logger.error("Create Agent: Missing Form Input Data")
        flash("Add a friend code out before submitting!", "danger")
        return False

    user_obj = UserSql.query.filter_by(friend_code=friend_code).first()

    if user_obj is None:
        flash("There is no user with the entered friend code. Try again!", "danger")
        return False

    # Don't need to bother if you're already friends!
    # TODO - Add another check here.
    if (
        Friends.query.filter_by(
            initiator_id=current_user.user_id, receiver_id=user_obj.user_id
        ).first()
        or Friends.query.filter_by(
            receiver_id=current_user.user_id, initiator_id=user_obj.user_id
        ).first()
    ):
        flash(f"You are already friends with {user_obj.username}.", "warning")
        return False

    # Don't send a new friend request if one was already sent...
    check_existing_outgoing = FriendRequests.query.filter_by(
        sender_id=current_user.user_id, recipient_id=user_obj.user_id
    ).first()

    if check_existing_outgoing:
        state = check_existing_outgoing.state
        # TODO - There's also a case where there could be an old friend request that was accepted
        # but the users stopped being friends. In that case its okay.
        if state == FriendRequestStates.PENDING.value:
            # flash("There is already a pending friend request.", "warning")
            flash(f"You already sent friend request to {user_obj.username}.", "warning")
            return False

    # Again, don't send if someone already sent you one first. No point in having two friend
    # request where each one is from the other.
    check_existing_incoming = FriendRequests.query.filter_by(
        recipient_id=current_user.user_id, sender_id=user_obj.user_id
    ).first()

    if check_existing_incoming:
        state = check_existing_incoming.state
        # TODO - There's also a case where there could be an old friend request that was accepted
        # but the users stopped being friends. In that case its okay.
        if state == FriendRequestStates.PENDING.value:
            # flash("There is already a pending friend request.", "warning")
            flash(
                f"{user_obj.username} already sent you a friend request. Respond to it!", "warning"
            )
            return False

    new_fr = FriendRequests()

    # Don't need to set state because its always pending to begin with.
    new_fr.sender_id = current_user.user_id
    new_fr.recipient_id = user_obj.user_id

    try:
        DATABASE.session.add(new_fr)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could not create Friend Request. Database Error!", "danger")
        return False

    subject = "Friend Request"
    friend_href = url_for("protected.system_friends")
    message = (
        f"<p>Hey, {current_user.first_name}! {user_obj.username} wants to be friends. Go to the "
        f'<a href="{friend_href}">Friends Page</a> to respond.</p>'
    )

    # TODO - Update DMs to alert users that they received a message via email.
    message_control.create_direct_message(new_fr.sender_id, new_fr.recipient_id, message, subject)

    return True


def create_new_friend(sender_id: int, recipient_id: int) -> bool:
    if Friends.query.filter_by(initiator_id=sender_id, receiver_id=recipient_id).first():
        logger.debug("Friend Relationship Already Exists!")
        return False
    elif Friends.query.filter_by(receiver_id=sender_id, initiator_id=recipient_id).first():
        logger.debug("Friend Relationship Already Exists!")
        return False
    else:
        new_friends = Friends()
        new_friends.initiator_id = sender_id
        new_friends.receiver_id = recipient_id

        try:
            DATABASE.session.add(new_friends)
            DATABASE.session.commit()
        except Exception as error:
            logger.critical(error)
            flash("Could not create Friend Database Error!", "danger")
            return False

    return True


def update_friend_request(object_id: int, payload: dict) -> bool:
    fr_qry = FriendRequests.query.filter_by(request_id=object_id)
    fr_obj = fr_qry.first()
    json_payload = json.loads(payload)

    if fr_obj is None:
        logger.error(f"Friend Request of ID, {object_id}, does not exist!")
        return False

    if "state" not in json_payload:
        logger.error("Missing state from payload.")
        return False

    new_status = json_payload["state"]

    if fr_obj.state != FriendRequestStates.PENDING.value:
        if fr_obj.state == FriendRequestStates.ACCEPTED.value:
            flash("Friend Request was already Accepted.", "info")
        elif fr_obj.state == FriendRequestStates.REJECTED.value:
            flash("Friend Request was rejected.", "info")
        elif fr_obj.state == FriendRequestStates.CANCELED.value:
            flash("Friend Request was already canceled.", "info")

        logger.error("Can only transition from PENDING state")
        return False

    if new_status == "ACCEPTED":
        result = create_new_friend(fr_obj.sender_id, fr_obj.recipient_id)

        if not result:
            logger.debug("Unable to create Friend via request object.")
            return False

        fr_qry.update({"state": FriendRequestStates.ACCEPTED.value})
        flash("Friend Request was Accepted.", "info")

    elif new_status == "REJECTED":
        fr_qry.update({"state": FriendRequestStates.REJECTED.value})
        flash("Friend Request was Rejected.", "info")
    elif new_status == "CANCELED":
        fr_qry.update({"state": FriendRequestStates.CANCELED.value})
        flash("Friend Request was Cancelled.", "info")

    try:
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could update Friend Request. Database Error!", "danger")
        return False

    return True


def delete_friend(object_id: int) -> bool:
    # Delete the friend record

    friend_obj = Friends.query.filter_by(friend_id=object_id).first()

    if friend_obj is None:
        logger.error(f"Cannot delete friend ID {object_id}. Does not exist!")
        return False

    # Eliminate friend from any owned groups.
    try:
        if current_user.user_id == friend_obj.initiator_id:
            delete_friend_user_id = friend_obj.receiver_id
        else:
            delete_friend_user_id = friend_obj.initiator_id
        logger.debug(f"Delete Friend: ID of Friend Being Deleted: {delete_friend_user_id}")
        group_control.remove_deleted_friend_from_groups(delete_friend_user_id)
    except Exception as error:
        logger.critical(error)
        return False

    return True

    try:
        DATABASE.session.delete(friend_obj)
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        return False

    subject = "No Longer Friends."
    message = f"{current_user.username}, has removed your from their friend list."
    friend_removed_id = 0

    if current_user.user_id == friend_obj.initiator_id:
        message_control.create_direct_message(
            current_user.user_id, friend_obj.receiver_id, message, subject
        )
        friend_removed_id = friend_obj.receiver_id
    else:
        message_control.create_direct_message(
            current_user.user_id, friend_obj.initiator_id, message, subject
        )
        friend_removed_id = friend_obj.initiator_id

    user_obj = UserSql.query.filter_by(user_id=friend_removed_id).first()

    flash(
        f"You and {user_obj.username} are no longer friends. A message was sent to let them know",
        "info",
    )

    return True
