from datetime import datetime, timezone

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Friends(PaginatedApi, DATABASE.Model):
    __tablename__ = "friends"

    friend_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    creation_date = DATABASE.Column(
        DATABASE.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )

    initiator_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
    receiver_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    def to_dict(self):
        return {
            "friend_id": self.friend_id,
            "creation_date": self.creation_date,
            "initiator_id": self.initiator_id,
            "receiver_id": self.receiver_id,
        }
