import os
import json
import shutil

from   config.logger       import log

from   config.orm          import db
from   models.upload_model import Media, MediaStatusEnum

from   utils.ffmpeg       import media2hls

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


        # decode the msg
        decoded_msg = json.loads(msg.value().decode("utf-8"))
        media_uuid  = decoded_msg["media_uuid"]
        media_type  = decoded_msg["media_type"]
        oauth_sub   = decoded_msg["oauth_sub"]

        log.info(f"kconsumer - media uuid <{media_uuid}> received for media2hls")


        # find the unprocessed file on disk
        uploaded_file_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", "temp/", f"{media_uuid}.dat")
        if not os.path.exists(uploaded_file_path):
            # delete dangling db record if file not found on disk
            thread_local_db_session.execute(db.delete(Media).where(Media.uuid == media_uuid))
            thread_local_db_session.commit()
            kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)])
            log.error(f"kconsumer - media uuid <{media_uuid}> not found on disk")
            continue

        # mark its db record as processing
        response = thread_local_db_session.execute(db.update(Media).where(Media.uuid == media_uuid).values(media_status=MediaStatusEnum.Processing.value))
        if response.rowcount >= 1:
            thread_local_db_session.commit()
        else:
            os.remove(uploaded_file_path)  # else, delete that dangling file if not found on db
            kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)])
            log.error(f"kconsumer - media uuid <{media_uuid}> not found in db")
            continue

        # craft output path
        output_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", f"{oauth_sub}/", f"{media_uuid}/")
        shutil.rmtree(output_path, ignore_errors=True)  # delete previous incomplete output (if any)
        # transcode it to HLS
        result = media2hls(uploaded_file_path, output_path , media_type, media_uuid)
        if result:
            #if successful, mark it on db as ready
            response = thread_local_db_session.execute(db.update(Media).where(Media.uuid == media_uuid).values(media_status=MediaStatusEnum.Ready.value))
            if response.rowcount >= 1:
                log.info(f"kconsumer - media uuid <{media_uuid}> is ready for playback")
            else:
                shutil.rmtree(output_path, ignore_errors=True)  # clear from disk on error
        else:
            thread_local_db_session.execute(db.delete(Media).where(Media.uuid == media_uuid))  # else delete from db
            log.error(f"kconsumer - media uuid <{media_uuid}> failed to transcode to HLS")


        thread_local_db_session.commit()
        os.remove(uploaded_file_path)  # and delete the original upload, regardless

        kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)])

