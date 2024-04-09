from datetime import datetime, timezone

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class GroupMembers(PaginatedApi, DATABASE.Model):
    __tablename__ = "group_members"

    group_member_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)
    creation_date = DATABASE.Column(
        DATABASE.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )

    group_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("groups.group_id"), nullable=False
    )
    member_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    def to_dict(self):
        return {
            "group_member_id": self.group_member_id,
            "active": self.active,
            "creation_date": self.creation_date,
            "group_id": self.group_id,
            "member_id": self.member_id,
        }
