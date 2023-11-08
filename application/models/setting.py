from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class SettingsSql(PaginatedApi, DATABASE.Model):
    __tablename__ = "settings"

    setting_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    name = DATABASE.Column(DATABASE.String(256), nullable=False, unique=True)
    pretty_name = DATABASE.Column(DATABASE.String(256), nullable=True)
    category = DATABASE.Column(DATABASE.String(256), nullable=True)
    description = DATABASE.Column(DATABASE.String(256), nullable=True)
    value = DATABASE.Column(DATABASE.String(256), nullable=True)
    data_type = DATABASE.Column(DATABASE.String(256), nullable=True)
