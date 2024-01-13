from datetime import datetime

from application.common import logger
from application.common.constants import AGENT_SMITH_DEFAULT_PORT
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.agent_group_member import AgentGroupMembers  # noqa: F401
from application.models.agent_friend_member import AgentFriendMembers  # noqa: F401


class Agents(PaginatedApi, DATABASE.Model):
    __tablename__ = "agents"

    agent_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # Identifying features
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)
    name = DATABASE.Column(DATABASE.String(256), nullable=False)
    hostname = DATABASE.Column(DATABASE.String(256), nullable=False)
    port = DATABASE.Column(DATABASE.Integer, nullable=False, default=AGENT_SMITH_DEFAULT_PORT)
    ssl_public_cert = DATABASE.Column(DATABASE.String(2048), nullable=False)
    access_token = DATABASE.Column(DATABASE.String(256), nullable=True)

    owner_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    groups_with_access = DATABASE.relationship(
        "AgentGroupMembers",
        foreign_keys="AgentGroupMembers.agent_id",
        backref="groups_with_access",
        lazy="dynamic",
    )

    friends_with_access = DATABASE.relationship(
        "AgentFriendMembers",
        foreign_keys="AgentFriendMembers.agent_id",
        backref="friends_with_access",
        lazy="dynamic",
    )

    def get_id(self):
        logger.debug(f"Called Agent.get_id: ID IS: {self.agent_id}")
        return str(self.agent_id)

    def is_active(self):
        return self.active

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "active": self.active,
            "creation_date": self.creation_date,
            "name": self.name,
            "hostname": self.hostname,
            "port": self.port,
            "access_token": self.access_token,
            "ssl_public_cert": self.ssl_public_cert,
            "owner_id": self.owner_id,
        }
