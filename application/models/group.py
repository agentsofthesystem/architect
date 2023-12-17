from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.group_member import GroupMembers  # noqa: F401


class Groups(PaginatedApi, DATABASE.Model):
    __tablename__ = "groups"

    group_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # Identifying features
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    name = DATABASE.Column(DATABASE.String(256), nullable=False)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    owner_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    members = DATABASE.relationship(
        "GroupMembers",
        foreign_keys="GroupMembers.group_id",
        backref="members",
        lazy="dynamic",
    )

    def to_dict(self):
        return {
            "group_id": self.group_id,
            "active": self.active,
            "name": self.name,
            "owner_id": self.owner_id,
            "creation_date": self.creation_date,
        }
