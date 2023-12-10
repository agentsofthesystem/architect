from flask import (
    Blueprint,
    jsonify,
)
from flask.views import MethodView
from flask_login import login_required

from application.api.controllers import agents
from application.common.tools import verified_required
from application.models.agent import Agents

backend = Blueprint("backend", __name__, url_prefix="/app/backend")


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
    "/agent/<int:object_id>",
    view_func=AgentsBackendApi.as_view("agents_api", Agents),
    methods=["GET", "DELETE"],
)
