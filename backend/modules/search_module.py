from flask import Blueprint
blueprint = Blueprint("search_module", __name__)


import os

from   flask                import request, jsonify

from   config.elasticsearch import esclient

from   config.orm           import db
from   models.user_model    import User

from   flask_jwt_extended   import jwt_required, get_jwt_identity




@blueprint.route("/api/v1/search/", methods=["get"])
def search_all_media():
    query = request.args.get("query")
    if not query:
        return { "status": "provide a ?query=" }, 422


    res = esclient.search(index=os.environ["ELASTICSEARCH_MAIN_INDEX"], body={
        "_source": {
            "excludes": ["media_ownedby_oauth_sub"]
        },
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["media_title^2", "media_uuid", "media_type"]
            }
        }
    })


    return jsonify(res["hits"]["hits"])


@blueprint.route("/api/v1/search/me/", methods=["get"])
@jwt_required()
def search_self_media():
    # verify ident
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    query = request.args.get("query")
    if not query:
        return { "status": "provide a ?query=" }, 422


    res = esclient.search(index=os.environ["ELASTICSEARCH_MAIN_INDEX"], body={
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query": query,
                        "fields": ["media_title^2", "media_uuid", "media_type"]
                    }
                },
                "filter": {
                    "term": { "media_ownedby_oauth_sub": user_oauth_sub }
                }
            }
        }
    })


    return jsonify(res["hits"]["hits"])

