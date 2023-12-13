from flask import Blueprint, jsonify, request
from flask.views import MethodView
from flask_login import login_required

from application.api.controllers import agents
from application.api.controllers import friends
from application.common.tools import verified_required
from application.models.agent import Agents
from application.models.friend_request import FriendRequests

backend = Blueprint("backend", __name__, url_prefix="/app/backend")


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
    "/friend/request/<int:object_id>",
    view_func=FriendRequestsBackendApi.as_view("friend_requests_api", FriendRequests),
    methods=["PATCH"],
)

backend.add_url_rule(
    "/agent/<int:object_id>",
    view_func=AgentsBackendApi.as_view("agents_api", Agents),
    methods=["GET", "DELETE"],
)
