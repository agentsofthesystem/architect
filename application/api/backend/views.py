from flask import Blueprint, jsonify, request
from flask.views import MethodView
from flask_login import login_required

from application.api.controllers import agents
from application.api.controllers import agent_control
from application.api.controllers import friends
from application.api.controllers import groups
from application.common import logger
from application.common.tools import verified_required
from application.models.agent import Agents
from application.models.agent import AgentFriendMembers
from application.models.agent import AgentGroupMembers
from application.models.friend import Friends
from application.models.group import Groups
from application.models.group_invite import GroupInvites
from application.models.group_member import GroupMembers
from application.models.friend_request import FriendRequests

backend = Blueprint("backend", __name__, url_prefix="/app/backend")


class GroupInvitesBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def post(self):
        if groups.resolve_group_invitation(request):
            return "", 204
        else:
            return "Error!", 500


class GameServerControlBackendApi(MethodView):
    def __init__(self) -> None:
        self.valid_commands = ["startup", "shutdown", "restart"]

    @login_required
    @verified_required
    def post(self, command):
        command_success = False

        if command not in self.valid_commands:
            logger.error(
                f"GameServerControlBackendApi: Command provided, {command}, not a valid command!"
            )
            return "Error!", 400

        if command == "startup":
            logger.info("Running startup command...")
            command_success = agent_control.startup(request)
        elif command == "shutdown":
            command_success = agent_control.shutdown(request)
        elif command == "restart":
            command_success = agent_control.restart(request)

        return ("Success", 204) if command_success else ("Error!", 500)


class AgentFriendMembersBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def delete(self, member_id):
        if agents.remove_friend_membership(member_id):
            return "", 204
        else:
            return "Error!", 500


class AgentGroupMembersBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def delete(self, member_id):
        if agents.remove_group_membership(member_id):
            return "", 204
        else:
            return "Error!", 500


class GroupMembersBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def delete(self, group_id, member_id):
        if groups.remove_user_from_group(group_id, member_id):
            return "", 204
        else:
            return "Error!", 500


class GroupsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def get(self, object_id):
        return jsonify(groups.get_group_by_id(object_id))

    @login_required
    @verified_required
    def patch(self, object_id):
        payload = request.json
        if groups.update_group(object_id, payload):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    @verified_required
    def delete(self, object_id):
        if groups.delete_group(object_id):
            return "", 204
        else:
            return "Error!", 500


class FriendsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def delete(self, object_id):
        if friends.delete_friend(object_id):
            return "", 204
        else:
            return "Error!", 500


class FriendRequestsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def patch(self, object_id):
        payload = request.json
        if friends.update_friend_request(object_id, payload):
            return "", 204
        else:
            return "Error!", 500


class AgentsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def get(self, object_id):
        return jsonify(agents.get_agent_by_id(object_id))

    @login_required
    @verified_required
    def delete(self, object_id):
        if agents.deactivate_agent(object_id):
            return "", 204
        else:
            return "Error!", 500


backend.add_url_rule(
    "/game/server/control/<string:command>",
    view_func=GameServerControlBackendApi.as_view("game_server_control_api"),
    methods=["POST"],
)

backend.add_url_rule(
    "/agent/friend/member/<int:member_id>",
    view_func=AgentFriendMembersBackendApi.as_view("agent_friend_members_api", AgentFriendMembers),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/agent/group/member/<int:member_id>",
    view_func=AgentGroupMembersBackendApi.as_view("agent_group_members_api", AgentGroupMembers),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/group/invite",
    view_func=GroupInvitesBackendApi.as_view("group_invites_api", GroupInvites),
    methods=["POST"],
)

backend.add_url_rule(
    "/group/member/<int:group_id>/<int:member_id>",
    view_func=GroupMembersBackendApi.as_view("group_members_api", GroupMembers),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/group/<int:object_id>",
    view_func=GroupsBackendApi.as_view("groups_api", Groups),
    methods=["GET", "PATCH", "DELETE"],
)

backend.add_url_rule(
    "/friend/<int:object_id>",
    view_func=FriendsBackendApi.as_view("friends_api", Friends),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/friend/request/<int:object_id>",
    view_func=FriendRequestsBackendApi.as_view("friend_requests_api", FriendRequests),
    methods=["PATCH"],
)

backend.add_url_rule(
    "/agent/<int:object_id>",
    view_func=AgentsBackendApi.as_view("agents_api", Agents),
    methods=["GET", "DELETE"],
)
