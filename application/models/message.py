from datetime import datetime

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class Messages(PaginatedApi, DATABASE.Model):
    __tablename__ = "messages"

    message_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    sender_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )
    recipient_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=True
    )

    subject = DATABASE.Column(DATABASE.String(256), nullable=False)
    message = DATABASE.Column(DATABASE.String(512), nullable=False)

    is_global = DATABASE.Column(DATABASE.Boolean, nullable=False)
    timestamp = DATABASE.Column(
        DATABASE.DateTime, index=True, default=datetime.utcnow, nullable=False
    )
