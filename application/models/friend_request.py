from datetime import datetime

from application.common.constants import FriendRequestState
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class FriendRequests(PaginatedApi, DATABASE.Model):
    __tablename__ = "friend_requests"

    request_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    state = DATABASE.Column(
        DATABASE.Integer, nullable=False, default=FriendRequestState.PENDING.value
    )

    sender_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
    recipient_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    timestamp = DATABASE.Column(
        DATABASE.DateTime, index=True, default=datetime.utcnow, nullable=False
    )
