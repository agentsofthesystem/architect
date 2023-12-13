from datetime import datetime

from application.common.constants import FriendRequestStates
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class FriendRequests(PaginatedApi, DATABASE.Model):
    __tablename__ = "friend_requests"

    request_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    state = DATABASE.Column(
        DATABASE.Integer, nullable=False, default=FriendRequestStates.PENDING.value
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

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
        }
