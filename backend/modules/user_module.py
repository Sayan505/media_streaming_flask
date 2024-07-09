from flask import Blueprint
blueprint = Blueprint("user_module", __name__)


from config.orm        import db
from models.user_model import User

from flask_jwt_extended import jwt_required, get_jwt_identity


@blueprint.route("/api/me", methods=["GET"])
@jwt_required()
def myinfo():
    oauth_sub = get_jwt_identity()
    user      = db.session.execute(db.select(User).filter_by(oauth_sub=oauth_sub)).scalar_one_or_none()
    if not user:
        return { "status": "invalid oauth identity" }, 401

    return {
        "display_name": user.display_name,
        "email": user.email
    }, 200

