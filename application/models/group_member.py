from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class GroupMembers(PaginatedApi, DATABASE.Model):
    __tablename__ = "group_members"

    group_member_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    creation_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    group_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("groups.group_id"), nullable=False
    )
    member_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
