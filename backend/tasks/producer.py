import os
import json

from   config.logger       import log

from   config.orm          import db
from   models.upload_model import Media, MediaStatusEnum

from   confluent_kafka     import Producer


kproducer = Producer({
    "bootstrap.servers": "kafka",
    "acks": "all",
    "enable.idempotence": True,
    "linger.ms": 0
})


def kafka_delivery_report_cb(err, msg):
    if err is not None:
        log.error(f"kproducer - message delivery error: {err}")
    else:
        # on msg delivered, mark the db record as queued
        media_uuid = json.loads(msg.value().decode("utf-8"))["media_uuid"]
        response   = db.session.execute(db.update(Media).where(Media.uuid == media_uuid).values(media_status=MediaStatusEnum.Queued.value))
        if response.rowcount >= 1:
            db.session.commit()
            log.info(f"kproducer - media uuid <{media_uuid}> successfully dispatched for media2hls")


def kproduce(encoded_msg_value):
        kproducer.produce(os.environ["KAFKA_TOPIC"], value=encoded_msg_value, callback=kafka_delivery_report_cb)
        kproducer.flush()

