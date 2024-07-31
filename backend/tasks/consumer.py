import os

from   config.logger       import log

from   config.orm          import db
from   models.upload_model import Pending, Media, MediaStatusEnum

from   confluent_kafka     import Consumer, TopicPartition


kconsumer = Consumer({
    "bootstrap.servers": "kafka",
    "group.id":          "group0",
    "client.id":         "consumer0",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False
})
kconsumer.subscribe([os.environ["KAFKA_TOPIC"]])


def kafka_consumer_routine(current_app_context):
    current_app_context.push()
    thread_local_db_session = db.session()
    while True:
        msg = kconsumer.poll()  # get msg

        if msg is None:
            continue
        if msg.error():
            log.error(f"kconsumer - msg consumer error: {msg.error()}")
            continue


        # decode the media_uuid from the msg
        media_uuid = msg.value().decode("utf-8")

        log.info(f"kconsumer - media uuid <{media_uuid}> received for media2hls")


        # find the unprocessed file on disk
        uploaded_file_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", "temp/", f"{media_uuid}.dat")
        if not os.path.exists(uploaded_file_path):
            # delete dangling db record if file not found on disk
            thread_local_db_session.execute(db.delete(Pending).where(Pending.uuid == media_uuid))
            thread_local_db_session.commit()
            kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset())])
            log.error(f"kconsumer - media uuid <{media_uuid}> not found on disk")
            continue

        # mark its db record as processing
        response = thread_local_db_session.execute(db.update(Pending).where(Pending.uuid == media_uuid).values(media_status=MediaStatusEnum.Processing.value))
        if response.rowcount >= 1:
            thread_local_db_session.commit()
        else:
            os.remove(uploaded_file_path)  # else, delete that dangling file if not found on db
            kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset())])
            log.error(f"kconsumer - media uuid <{media_uuid}> not found in db")
            continue


        # transcode it to HLS
        result = media2hls(uploaded_file_path)
        if result:
            #if successful, mark it on db as ready (TODO: transfer record to Media table)
            response = thread_local_db_session.execute(db.update(Pending).where(Pending.uuid == media_uuid).values(media_status=MediaStatusEnum.Ready.value))
            thread_local_db_session.commit()
            log.info(f"kconsumer - media uuid <{media_uuid}> is ready for playback")
        else:
            thread_local_db_session.execute(db.delete(Pending).where(Pending.uuid == media_uuid))  # else delete from db
            thread_local_db_session.commit()
            log.error(f"kconsumer - media uuid <{media_uuid}> failed to transcode to HLS")


        os.remove(uploaded_file_path)  # and delete the file, regardless

        kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset())])




def media2hls(uploaded_file_path):
    #if not os.path.exists(temp_upload_path):
        #os.mkdir(temp_upload_path)
    # then move it to the /storage/sub/uuid.mp4 OR delete if failed
    log.info(f"<<<<<{uploaded_file_path}>>>>>")

    return True

