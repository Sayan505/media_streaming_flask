from config.logger      import log

from flask_jwt_extended import jwt_required, get_jwt_identity 

from flask import Blueprint
blueprint = Blueprint("user_module", __name__)


@blueprint.route("/api/me", methods=["GET"])
@jwt_required()
def myinfo():
    sub = get_jwt_identity()
    
    return sub, 200

