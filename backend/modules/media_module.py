from flask import Blueprint
blueprint = Blueprint("hls_module", __name__)


import os
import subprocess
import json
from   uuid                import uuid4

from   flask               import request

from   flask_jwt_extended  import jwt_required, get_jwt_identity

from   config.logger       import log

from   config.orm          import db
from   models.user_model   import User
from   models.upload_model import Pending, Media, MediaStatusEnum, MediaTypeEnum

from   tasks.producer      import kproduce


ALLOWED_EXTS = { "mp4", "avi", "mp3", "ogg", "flac", "wav" }
def allowed_filetype(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS

def get_media_type(uploaded_file_path):
    try:
        cmdstr = f"ffprobe -print_format json -v quiet -show_format -show_streams {uploaded_file_path}"
        proc   = subprocess.run(cmdstr, capture_output=True, shell=True, timeout=3)
        if proc.returncode != 0:
            return None

        probe   = json.loads(proc.stdout.decode("utf-8"))

        streams = probe["streams"]
        if len(streams) <= 0:
            return None

        audio_nstreams = 0
        video_nstreams = 0

        for stream in streams:
            codec_type = stream["codec_type"]

            if codec_type == "audio":
                audio_nstreams += 1
            elif codec_type == "video":
                video_nstreams += 1
            else:
                return None


        if audio_nstreams == 1 and video_nstreams == 0:
            return MediaTypeEnum.Audio
        elif audio_nstreams == 1 and video_nstreams == 1:
            return MediaTypeEnum.Video
        else:
            return None


    except subprocess.TimeoutExpired:
        return None




# media handling routes
@blueprint.route("/api/v1/media", methods=["GET", "POST", "PUT", "DELETE"])
@jwt_required(optional=True)
def media():
    # upload new media
    if request.method == "POST":
        oauth_sub = get_jwt_identity()
        user      = db.session.execute(db.select(User.oauth_sub).filter_by(oauth_sub=oauth_sub)).scalar_one_or_none()
        if not user:
            return { "status": "invalid oauth identity" }, 401


        if "file" not in request.files:
            return { "status": "file not supplied" }, 400

        file       = request.files["file"]
        title      = request.form["title"] if "title" in request.form else "Untitled Upload"
        media_uuid = str(uuid4())

        if file and file.filename == "":
            return { "status": "file not supplied correctly" }, 400

        if not allowed_filetype(file.filename):
            return { "status": "disallowed filetype" }, 422


        # save unprocessed files to temp
        uploaded_file_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", "temp/", f"{media_uuid}.dat")
        file.save(uploaded_file_path)

        media_type_enum = get_media_type(uploaded_file_path)  # then probe it
        if not media_type_enum:
            os.remove(uploaded_file_path)
            return { "status": "media file could not be parsed" }, 422


        # create db record (before dispatching for media2hls)
        pending                   = Pending()
        pending.uuid              = media_uuid
        pending.ownedby_oauth_sub = oauth_sub
        pending.media_type        = media_type_enum.value
        pending.title             = title
        pending.media_status      = MediaStatusEnum.NotQueued.value
        db.session.add(pending)
        db.session.commit()
   
        log.info(f"new upload created as media_uuid: <{media_uuid}> - <{oauth_sub}>")


        # then dispatch for media2hls through kafka
        kproduce(encoded_msg_value=media_uuid.encode("utf-8"))


        return { "status": "queued", "detected_media_type": media_type_enum.value }, 200

