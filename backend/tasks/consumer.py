import os
import subprocess
import json

from   config.logger       import log

from   config.orm          import db
from   models.upload_model import Media, MediaStatusEnum

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


        # transcode it to HLS
        result = media2hls(uploaded_file_path, os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", f"{oauth_sub}/", f"{media_uuid}/"), media_uuid)
        if result:
            #if successful, mark it on db as ready
            response = thread_local_db_session.execute(db.update(Media).where(Media.uuid == media_uuid).values(media_status=MediaStatusEnum.Ready.value))
            log.info(f"kconsumer - media uuid <{media_uuid}> is ready for playback")
        else:
            thread_local_db_session.execute(db.delete(Media).where(Media.uuid == media_uuid))  # else delete from db
            log.error(f"kconsumer - media uuid <{media_uuid}> failed to transcode to HLS")


        thread_local_db_session.commit()
        os.remove(uploaded_file_path)  # and delete the original upload, regardless

        kconsumer.commit(offsets=[TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)])




def media2hls(uploaded_file_path, output_folder, media_uuid):
    log.info(f"kconsumer - media uuid <{media_uuid}> is currently being encoded ...")

    # set up output dir
    os.makedirs(output_folder, exist_ok=True)

    # encode to HLS!
    cmdstr = f"ffmpeg -y -i {uploaded_file_path} -map 0:v:0? -map 0:a:0? -preset fast -codec:v libx264 -crf 22 -codec:a aac -b:a 128k -ac 2 -ar 48000 -hls_time 10 -hls_playlist_type vod -hls_flags independent_segments -f hls {output_folder}/playlist.m3u8"
    proc   = subprocess.run(cmdstr, capture_output=True, shell=True)
    if proc.returncode != 0:
        return False

    return True

