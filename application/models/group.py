from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Groups(PaginatedApi, DATABASE.Model):
    __tablename__ = "groups"

    group_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # Identifying features
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    owner_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    owner = DATABASE.relationship(
        "UserSql",
        foreign_keys="UserSql.user_id",
        backref="owner",
        lazy="dynamic",
    )

    members = DATABASE.relationship(
        "GroupMembers",
        foreign_keys="GroupMembers.group_id",
        backref="members",
        lazy="dynamic",
    )
