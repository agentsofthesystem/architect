from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class MonitorFault(PaginatedApi, DATABASE.Model):
    __tablename__ = "monitor_faults"

    monitor_fault_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    monitor_id = DATABASE.Column(
        DATABASE.Integer, DATABASE.ForeignKey("monitors.monitor_id"), nullable=False
    )
