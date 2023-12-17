from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class AgentGroupMembers(PaginatedApi, DATABASE.Model):
    __tablename__ = "agent_group_members"

    agent_group_member_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    agent_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("agents.agent_id"), nullable=False
    )
    group_member_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("groups.group_id"), nullable=False
    )

    def to_dict(self):
        return {
            "agent_group_member_id": self.agent_group_member_id,
            "active": self.active,
            "creation_date": self.creation_date,
            "agent_id": self.agent_id,
            "group_member_id": self.group_member_id,
        }
