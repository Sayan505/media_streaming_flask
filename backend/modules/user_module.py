from flask import Blueprint
blueprint = Blueprint("user_module", __name__)

import string

from   flask               import request

from   config.orm          import db
from   models.upload_model import Media
from   models.user_model   import User

from   flask_jwt_extended  import jwt_required, get_jwt_identity


def display_name_filter(display_name):
    allowed_charset = set(string.ascii_letters + string.digits + string.punctuation + ' ')

    display_name = display_name.strip()
    if not (len(display_name) >= 3 and len(display_name) <= 32):
        return None, "display_name should be alteast 3 characters long and within 32 characters"

    if set(display_name) <= allowed_charset:
        return display_name, None
    else: return None, "display_name contains disallowed characters"




@blueprint.route("/api/v1/me", methods=["GET"])
@jwt_required()
def view_self_info():
    jwt_oauth_sub  = get_jwt_identity()
    user           = db.session.execute(db.select(User).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user:
        return { "status": "invalid oauth identity" }, 401

    return {
        "display_name": user.display_name,
        "email":        user.email
    }, 200


@blueprint.route("/api/v1/me", methods=["PUT"])
@jwt_required()
def edit_self_info():
    # verify ident
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    # parse req json body
    req_json = request.get_json(force=True, silent=True, cache=False)
    if not req_json:
        return { "status": "bad request" }, 400

    if "display_name" not in req_json:
        return { "status": "display_name not supplied" }, 400

    new_display_name  = req_json["display_name"]

    new_display_name_filtered = display_name_filter(new_display_name)
    if not new_display_name_filtered[0]:
        return { "status": new_display_name_filtered[1] }, 422


    # exec query (match by user ident)
    response = db.session.execute(db.update(User).where(User.oauth_sub == user_oauth_sub).values(display_name=new_display_name_filtered))
    if response.rowcount >= 1:
        db.session.commit()
        return { "status": "success" }, 200

    return { "status": "bad request" }, 400


@blueprint.route("/api/v1/me/uploads", methods=["GET"])
@jwt_required()
def get_self_uploads():
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    # parse arg for request page
    page = request.args.get("page", default=1, type=int)


    # exec query
    paged_response = (Media.query
        .with_entities(Media.uuid, Media.media_type, Media.title, Media.media_status)
        .filter(Media.ownedby_oauth_sub == user_oauth_sub)
        .order_by(Media.media_status.asc())
        .paginate(page=page, per_page=10))


    # serialize response
    items = [{
        "media_uuid":   row.uuid,
        "media_type":   row.media_type,
        "title":        row.title,
        "media_status": row.media_status
    } for row in paged_response.items]


    # return response
    return {
        "status":       "success",
        "current_page": page,
        "npages":       paged_response.pages,
        "items":        items
    }, 200

