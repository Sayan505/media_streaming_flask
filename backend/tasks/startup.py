import os
import json

from   config.logger                 import log

from   config.orm                    import db
from   models.upload_model           import Media, MediaStatusEnum

from   models.elasticsearch_mappings import mappings
from   config.elasticsearch          import esclient

from   tasks.producer                import kproduce

def init_elasticsearch():
    log.info(f"elasticsearch - {esclient.info()}")

    esindex = os.environ["ELASTICSEARCH_MAIN_INDEX"]

    # create mappings if not exists
    if not esclient.indices.exists(index=esindex):
        esclient.indices.create(index=esindex, mappings=mappings)
        log.info(f"elasticsearch - index created: {esindex}")


def resume_kafka_consumer_task(current_app_context):
    current_app_context.push()
    local_scoped_db_session = db.session()

    # produce msg for only the rows which have NOT been produced to kafka and was left at being marked as "Created"
    for media in local_scoped_db_session.query(Media).filter(Media.media_status == MediaStatusEnum.Created.value).yield_per(1000):
        msg_value = {
            "media_uuid": media.uuid,
            "media_type": media.media_type,
            "oauth_sub":  media.ownedby_oauth_sub
        }
        msg_value_json = json.dumps(msg_value)
        kproduce(encoded_msg_value=msg_value_json.encode("utf-8"))


def resume_svcs(current_app_context):
    init_elasticsearch()
    resume_kafka_consumer_task(current_app_context)

