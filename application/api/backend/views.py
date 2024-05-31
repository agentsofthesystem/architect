from flask import Blueprint, jsonify, request
from flask.views import MethodView
from flask_login import login_required

from application.api.controllers import agents
from application.api.controllers import agent_control
from application.api.controllers import agent_logs
from application.api.controllers import friends
from application.api.controllers import groups
from application.api.controllers import monitors
from application.api.controllers import monitor_attributes
from application.api.controllers import monitor_faults
from application.api.controllers import properties
from application.common import logger
from application.common.decorators import verified_required
from application.models.agent import Agents
from application.models.agent_friend_member import AgentFriendMembers
from application.models.agent_group_member import AgentGroupMembers
from application.models.agent_log import AgentLog
from application.models.friend import Friends
from application.models.friend_request import FriendRequests
from application.models.group import Groups
from application.models.group_invite import GroupInvites
from application.models.group_member import GroupMembers
from application.models.monitor import Monitor
from application.models.monitor_attribute import MonitorAttribute
from application.models.monitor_fault import MonitorFault
from application.models.property import Property


backend = Blueprint("backend", __name__, url_prefix="/app/backend")


class AgentLogsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def delete(self, agent_id):
        if agent_logs.delete_all_agent_logs(agent_id):
            return "", 204
        else:
            return "Error!", 500


class MonitorFaultsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    @verified_required
    def get(self, agent_id, monitor_type):
        return jsonify(monitor_faults.get_monitor_faults(agent_id, monitor_type))

    @login_required
    @verified_required
    def delete(self, agent_id, monitor_type, fault_id):
        if monitor_faults.deactivate_monitor_fault(agent_id, monitor_type, fault_id):
            return "", 204
        else:
            return "Error!", 500


class MonitorAttributesBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    def post(self, agent_id, monitor_type):
        payload = request.json
        if monitor_attributes.attach_attribute_to_monitor(agent_id, monitor_type, payload):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    def patch(self, agent_id, monitor_type):
        payload = request.json
        if monitor_attributes.update_monitor_attribute(agent_id, monitor_type, payload):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    def delete(self, agent_id, monitor_type):
        payload = request.json
        if monitor_attributes.remove_attribute_from_monitor(agent_id, monitor_type, payload):
            return "", 204
        else:
            return "Error!", 500


class MonitorsBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    def post(self, agent_id, monitor_type):
        if monitors.create_monitor(agent_id, monitor_type):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    def delete(self, agent_id, monitor_type):
        if monitors.disable_monitor(agent_id, monitor_type):
            return "", 204
        else:
            return "Error!", 500


class PropertiesBackendApi(MethodView):
    def __init__(self, model):
        self.model = model

    @login_required
    def post(self, user_id, property_name):
        payload = request.json
        if properties.create_property(user_id, property_name, payload):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    def patch(self, user_id, property_name):
        payload = request.json
        if properties.update_property(user_id, property_name, payload):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    def delete(self, user_id, property_name):
        if properties.delete_property(user_id, property_name):
            return "", 204
        else:
            return "Error!", 500


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
        self.valid_commands = ["startup", "shutdown", "restart", "update"]

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
            command_success = agent_control.startup(request)
        elif command == "shutdown":
            command_success = agent_control.shutdown(request)
        elif command == "restart":
            command_success = agent_control.restart(request)
        elif command == "update":
            command_success = agent_control.update(request)

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
    def patch(self, object_id):
        if agents.reactivate_agent(object_id):
            return "", 204
        else:
            return "Error!", 500

    @login_required
    @verified_required
    def delete(self, object_id):
        if agents.deactivate_agent(object_id):
            return "", 204
        else:
            return "Error!", 500


backend.add_url_rule(
    "/agent/logs/clear/<int:agent_id>",
    view_func=AgentLogsBackendApi.as_view("agent_logs_api", AgentLog),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/monitor/<int:agent_id>/<string:monitor_type>",
    view_func=MonitorsBackendApi.as_view("agent_monitor_api", Monitor),
    methods=["DELETE", "POST"],
)

backend.add_url_rule(
    "/monitor/attribute/<int:agent_id>/<string:monitor_type>",
    view_func=MonitorAttributesBackendApi.as_view("agent_monitor_attribute_api", MonitorAttribute),
    methods=["DELETE", "POST", "PATCH"],
)

backend.add_url_rule(
    "/monitor/fault/<int:agent_id>/<string:monitor_type>",
    view_func=MonitorFaultsBackendApi.as_view("agent_monitor_fault_inquiry_api", MonitorFault),
    methods=["GET"],
)

backend.add_url_rule(
    "/monitor/fault/<int:agent_id>/<string:monitor_type>/<int:fault_id>",
    view_func=MonitorFaultsBackendApi.as_view("agent_monitor_fault_api", MonitorFault),
    methods=["DELETE"],
)

backend.add_url_rule(
    "/property/<int:user_id>/<string:property_name>",
    view_func=PropertiesBackendApi.as_view("user_properties_api", Property),
    methods=["DELETE", "POST", "PATCH"],
)

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
    methods=["GET", "PATCH", "DELETE"],
)
