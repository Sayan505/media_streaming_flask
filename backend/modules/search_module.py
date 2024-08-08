from flask import Blueprint
blueprint = Blueprint("search_module", __name__)


import os

from   flask                import request, jsonify
from   config.elasticsearch import esclient




@blueprint.route("/api/v1/search/", methods=["GET"])
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

