from application.common.pagination import PaginatedApi
from application.extensions import DATABASE


class BetaUser(PaginatedApi, DATABASE.Model):
    __tablename__ = "beta_users"

    beta_user_id = DATABASE.Column(DATABASE.Integer, primary_key=True)

    # User Login Stuff
    active = DATABASE.Column(DATABASE.Boolean, nullable=False, default=False)
    email = DATABASE.Column(DATABASE.String(256), unique=True, nullable=False)
