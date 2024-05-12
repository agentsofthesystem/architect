import pytz

from datetime import datetime, timezone

from application.common import constants
from application.common.pagination import PaginatedApi
from application.extensions import DATABASE
from application.models.user import UserSql


class AgentLog(PaginatedApi, DATABASE.Model):
    __tablename__ = "agent_logs"

    log_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    agent_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("agents.agent_id"), nullable=False
    )

    user_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("users.user_id"), nullable=False
    )

    timestamp = DATABASE.Column(
        DATABASE.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )

    is_automated = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)

    message = DATABASE.Column(DATABASE.String(256), nullable=False)

    def to_dict(self, time_format_str=constants.DEFAULT_TIME_FORMAT_STR, timezone=None):
        user_obj = UserSql.query.filter_by(user_id=self.user_id).first()

        if timezone:
            local_tz = pytz.timezone(timezone)
            timestamp_local = self.timestamp.astimezone(local_tz)
            timestamp_str = timestamp_local.strftime(time_format_str)
        else:
            timestamp_str = self.timestamp.strftime(time_format_str)

        return {
            "log_id": self.log_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "username": user_obj.username,
            "timestamp": timestamp_str,
            "is_automated": self.is_automated,
            "message": self.message,
        }
