from datetime import datetime

from application.common import logger
from application.common.constants import AGENT_SMITH_DEFAULT_PORT
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Agents(PaginatedApi, DATABASE.Model):
    __tablename__ = "agents"

    agent_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # Identifying features
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow())
    hostname = DATABASE.Column(DATABASE.String(256), nullable=False)
    port = DATABASE.Column(DATABASE.Integer, nullable=False, default=AGENT_SMITH_DEFAULT_PORT)
    access_token = DATABASE.Column(DATABASE.String(256), nullable=True)

    owner_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    owner = DATABASE.relationship(
        "UserSql",
        foreign_keys="UserSql.user_id",
        backref="owner",
        lazy="dynamic",
    )

    # To track sharing - TODO - Will need an intermediate table for each.
    # Friend to Agent (Direct)
    # Group to Agent

    # friends = DATABASE.relationship(
    #     "Friends",
    #     foreign_keys="Friends.friend_id",
    #     backref="friends",
    #     lazy="dynamic",
    # )

    # groups = DATABASE.relationship(
    #     "Groups",
    #     foreign_keys="Groups.group_id",
    #     backref="groups",
    #     lazy="dynamic",
    # )

    def get_id(self):
        logger.debug(f"Called Agent.get_id: ID IS: {self.agent_id}")
        return str(self.agent_id)

    def is_active(self):
        return self.active
