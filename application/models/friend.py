from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Friends(PaginatedApi, DATABASE.Model):
    __tablename__ = "friends"

    friend_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    created_date = DATABASE.Column(DATABASE.DateTime, nullable=False, default=datetime.utcnow)

    myself_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
    friends_with_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
