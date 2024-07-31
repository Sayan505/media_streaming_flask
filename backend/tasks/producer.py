import os

from   config.logger       import log

from   config.orm          import db
from   models.upload_model import Pending, MediaStatusEnum

from   confluent_kafka     import Producer


kproducer = Producer({
    "bootstrap.servers": "kafka",
    "acks": "all",
    "linger.ms": 0
})


def kafka_delivery_report_cb(err, msg):
    if err is not None:
        log.error(f"kproducer - message delivery error: {err}")
    else:
        media_uuid = msg.value().decode("utf-8")
        pending    = db.session.execute(db.select(Pending).filter_by(uuid=media_uuid)).scalar_one_or_none()
        if pending:
            pending.media_status = MediaStatusEnum.Queued.value  # mark as queued
            db.session.commit()
            log.info(f"kproducer - media uuid <{media_uuid}> successfully dispatched for media2hls")


def kproduce(encoded_msg_value):
        kproducer.produce(os.environ["KAFKA_TOPIC"], value=encoded_msg_value, callback=kafka_delivery_report_cb)
        kproducer.flush()

