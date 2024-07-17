from flask import Blueprint
blueprint = Blueprint("hls_module", __name__)


import os
import subprocess
import json
from uuid                import uuid4

from flask               import request 

from config.logger       import log

from config.orm          import db
from models.user_model   import User
from models.upload_model import Media, MediaTypeEnum

from flask_jwt_extended  import jwt_required, get_jwt_identity


ALLOWED_EXTS = { "mp4", "avi", "mp3", "ogg", "flac", "wav" }
def allowed_filetype(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS


def get_media_type(uploaded_file_path):
    try:
        cmdstr = f"ffprobe -print_format json -v quiet -show_format -show_streams {uploaded_file_path}"
        proc   = subprocess.run(cmdstr, capture_output=True, shell=True, timeout=3)
        if proc.returncode != 0:
            return None


        probe   = json.loads(proc.stdout)

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
        elif audio_nstreams <= 1 and video_nstreams == 1:
            return MediaTypeEnum.Video
        else:
            return None


    except subprocess.TimeoutExpired:
        return None


def media2hls():
    pass


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

        file = request.files["file"]
        media_uuid = uuid4()

        if file and file.filename == "":
            return { "status": "file not supplied correctly" }, 400

        if not allowed_filetype(file.filename):
            return { "status": "disallowed filetype" }, 422


        uploaded_file_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/temp/", f"{str(media_uuid)}.dat")  # upload unprobed files to temp
        file.save(uploaded_file_path)

        media_type = get_media_type(uploaded_file_path)  # then probe it
        if not media_type:
            os.remove(uploaded_file_path)
            return { "status": "media file could not be parsed" }, 422

        # create db record in the seperate pending table(yet to reencode to hls)
        # then move it to the /storage/sub/uuid.mp4 OR delete if failed

        return { "status": media_type }, 200

