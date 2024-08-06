import os

from elasticsearch     import Elasticsearch


esclient = Elasticsearch(
    "http://elasticsearch:9200",
    http_auth=("elastic", os.environ["ELASTICSEARCH_PASSWORD"])
)

