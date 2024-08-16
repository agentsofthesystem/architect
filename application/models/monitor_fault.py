from flask_admin.contrib.sqla import ModelView

from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class MonitorFault(PaginatedApi, DATABASE.Model):
    __tablename__ = "monitor_faults"

    monitor_fault_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    monitor_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("monitors.monitor_id"), nullable=False
    )

    fault_time = DATABASE.Column(DATABASE.DateTime, nullable=False)

    fault_description = DATABASE.Column(DATABASE.String(256), nullable=False)

    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "monitor_fault_id": self.monitor_fault_id,
            "monitor_id": self.monitor_id,
            "fault_time": self.fault_time,
            "fault_description": self.fault_description,
            "active": self.active,
        }


class MonitorFaultView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = MonitorFault.__table__.columns.keys()
