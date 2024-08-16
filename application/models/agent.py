from datetime import datetime, timezone
from flask_admin.contrib.sqla import ModelView

from application.common import logger
from application.common.constants import AGENT_SMITH_DEFAULT_PORT
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.agent_group_member import AgentGroupMembers  # noqa: F401
from application.models.agent_friend_member import AgentFriendMembers  # noqa: F401
from application.models.group import Groups  # noqa: F401


class Agents(PaginatedApi, DATABASE.Model):
    __tablename__ = "agents"

    agent_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # Identifying features
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(
        DATABASE.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    name = DATABASE.Column(DATABASE.String(256), nullable=False)
    hostname = DATABASE.Column(DATABASE.String(256), nullable=False)
    port = DATABASE.Column(DATABASE.Integer, nullable=False, default=AGENT_SMITH_DEFAULT_PORT)
    ssl_public_cert = DATABASE.Column(DATABASE.String(2048), nullable=False)
    access_token = DATABASE.Column(DATABASE.String(256), nullable=True)

    owner_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    monitors = DATABASE.relationship(
        "Monitor", foreign_keys="Monitor.agent_id", backref="monitors", lazy="dynamic"
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

    attached_monitors = DATABASE.relationship(
        "Monitor",
        foreign_keys="Monitor.agent_id",
        backref="attached_monitors",
        lazy="dynamic",
    )

    @property
    def num_users(self):
        return self.get_users()

    def get_users(self, as_list=False):
        unique_user_ids = []
        group_member_id_list = [group.group_member_id for group in self.groups_with_access.all()]
        friend_id_list = [friend.friend_member_id for friend in self.friends_with_access.all()]

        for friend_id in friend_id_list:
            if friend_id not in unique_user_ids:
                unique_user_ids.append(friend_id)

        # For each group_member_id in group_member_id_list, get the groups.
        for group_member_id in group_member_id_list:
            group_obj = Groups.query.filter_by(group_id=group_member_id).first()
            members = group_obj.members.all()
            for member in members:
                member_id = member.member_id
                if member_id not in unique_user_ids:
                    unique_user_ids.append(member_id)

        # Do not count the agent owner user_id
        if self.owner_id in unique_user_ids:
            unique_user_ids.remove(self.owner_id)

        if as_list:
            return unique_user_ids
        else:
            return len(unique_user_ids)

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


class AgentView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = Agents.__table__.columns.keys()
