import os

from   config.logger                 import log

from   models.elasticsearch_mappings import mappings
from   config.elasticsearch          import esclient


def init_elasticsearch():
    log.info(f"elasticsearch - {esclient.info()}")

    esindex = os.environ["ELASTICSEARCH_MAIN_INDEX"]

    # create mappings if not exists
    if not esclient.indices.exists(index=esindex):
        esclient.indices.create(index=esindex, mappings=mappings)
        log.info(f"elasticsearch - index created: {esindex}")


def resume_kafka_consumer():
    pass


def resume_svcs():
    init_elasticsearch()
    resume_kafka_consumer()

