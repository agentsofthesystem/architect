from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class DefaultProperty(PaginatedApi, DATABASE.Model):
    __tablename__ = "default_properties"

    default_property_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    property_name = DATABASE.Column(DATABASE.String(256), nullable=False)

    property_type = DATABASE.Column(DATABASE.String(256), nullable=False)

    property_default_value = DATABASE.Column(DATABASE.String(256), nullable=False)

    property_description = DATABASE.Column(DATABASE.String(256), nullable=False)
