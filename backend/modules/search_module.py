from flask import Blueprint
blueprint = Blueprint("search_module", __name__)


import os
import math

from   flask                import request, jsonify

from   config.elasticsearch import esclient

from   config.orm           import db
from   models.user_model    import User

from   flask_jwt_extended   import jwt_required, get_jwt_identity




@blueprint.route("/api/v1/search/", methods=["GET"])
def search_all_media():
    query = request.args.get("q")
    if not query:
        return { "status": "provide a ?q=" }, 422

    page = request.args.get("p", 0, type=int)
    size = 10  # items per page


    res = esclient.search(index=os.environ["ELASTICSEARCH_MAIN_INDEX"], body={
        "_source": {
            "excludes": ["media_ownedby_oauth_sub"]
        },
        "query": {
            "multi_match": {
                "query":  query,
                "fields": ["media_title^2", "media_uuid", "media_type"]
            }
        }
    }, from_=page*size, size=size)

    nhits  = res["hits"]["total"]["value"] 
    npages = math.ceil(nhits / size)

    if page < 0: page = 0
    elif page > npages: page = npages


    return jsonify({
        "current_page":  page,
        "npages":        npages,
        "nhits":         nhits,
        "hits":          res["hits"]["hits"]
    })


@blueprint.route("/api/v1/search/me/", methods=["GET"])
@jwt_required()
def search_self_media():
    # verify ident
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    query = request.args.get("q")
    if not query:
        return { "status": "provide a ?q=" }, 422

    page = request.args.get("p", 0, type=int)
    size = 10  # items per page


    res = esclient.search(index=os.environ["ELASTICSEARCH_MAIN_INDEX"], body={
        "query": {
            "bool": {
                "must": {
                    "multi_match": {
                        "query":  query,
                        "fields": ["media_title^2", "media_uuid", "media_type"]
                    }
                },
                "filter": {
                    "term": { "media_ownedby_oauth_sub": user_oauth_sub }
                }
            }
        }
    }, from_=page*size, size=size)


    nhits  = res["hits"]["total"]["value"] 
    npages = math.ceil(nhits / size)

    if page < 0: page = 0
    elif page > npages: page = npages


    return jsonify({
        "current_page":  page,
        "npages":        npages,
        "nhits":         nhits,
        "hits":          res["hits"]["hits"]
    })

