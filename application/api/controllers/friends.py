import json
import uuid

from flask import flash
from flask_login import current_user

from application.common import logger
from application.common.constants import FriendRequestStates
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
    initiated_friends = current_user.initiated_friends.all()
    received_friends = current_user.received_friends.all()

    all_friends = initiated_friends + received_friends

    final_list = []

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

    # TODO - Send Email

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
        logger.error("Can only transition from PENDING state")
        return False

    if new_status == "ACCEPTED":
        result = create_new_friend(fr_obj.sender_id, fr_obj.recipient_id)

        if not result:
            logger.debug("Unable to create Friend via request object.")
            return False

        fr_qry.update({"state": FriendRequestStates.ACCEPTED.value})
    elif new_status == "REJECTED":
        fr_qry.update({"state": FriendRequestStates.REJECTED.value})
    elif new_status == "CANCELED":
        fr_qry.update({"state": FriendRequestStates.CANCELED.value})

    try:
        DATABASE.session.commit()
    except Exception as error:
        logger.critical(error)
        flash("Could update Friend Request. Database Error!", "danger")
        return False

    return True
