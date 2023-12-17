from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class AgentFriendMembers(PaginatedApi, DATABASE.Model):
    __tablename__ = "agent_friend_members"

    agent_friend_member_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    agent_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("agents.agent_id"), nullable=False
    )
    friend_member_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    def to_dict(self):
        return {
            "agent_friend_member_id": self.agent_friend_member_id,
            "active": self.active,
            "creation_date": self.creation_date,
            "agent_id": self.agent_id,
            "friend_member_id": self.friend_member_id,
        }
