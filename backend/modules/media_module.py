from flask import Blueprint
blueprint = Blueprint("hls_module", __name__)


import os
import subprocess
import json
import string
from   uuid                import uuid4

from   flask               import request, make_response, send_from_directory

from   flask_jwt_extended  import jwt_required, get_jwt_identity

from   config.logger       import log

from   config.orm          import db
from   models.user_model   import User
from   models.upload_model import Media, MediaStatusEnum, MediaTypeEnum

from   tasks.producer      import kproduce


ALLOWED_EXTS = { "mp4", "avi", "mp3", "ogg", "flac", "wav" }
def allowed_filetype(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS

def title_filter(title):
    allowed_charset = set(string.ascii_letters + string.digits + string.punctuation + ' ')

    title = title.strip()
    if not (len(title) >= 4 and len(title) <= 100):
        return None, "title should be alteast 4 characters long and within 100 characters"

    if set(title) <= allowed_charset:
        return title, None
    else: return None, "title contains disallowed characters"


# TODO: refactor to distinguish b/w thumbnails in mp3s vs video streams
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




@blueprint.route("/api/v1/media", methods=["POST"])
@jwt_required()
def upload_new_media():
    # verify identity
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "unauthorized" }, 401


    # get request form fields
    if "file" not in request.files:
        return { "status": "file not supplied" }, 400

    file             = request.files["file"]
    requested_title  = request.form["title"] if "title" in request.form else "Untitled Upload"


    # validate request form fields
    if file and file.filename == "":
        return { "status": "file not supplied correctly" }, 400

    if not allowed_filetype(file.filename):
        return { "status": "disallowed filetype" }, 422

    title = title_filter(requested_title)
    if not title[0]:
        return { "status": title[1] }, 422


   # gen uuid for the upload
    media_uuid = str(uuid4())


    # save unprocessed files to temp
    uploaded_file_path = os.path.join(f"{os.environ["UPLOAD_FOLDER"]}/", "temp/", f"{media_uuid}.dat")
    file.save(uploaded_file_path)

    # then probe it
    media_type_enum = get_media_type(uploaded_file_path)
    if not media_type_enum:
        os.remove(uploaded_file_path)
        return { "status": "media file could not be parsed" }, 422


    # create db record (before dispatching for media2hls)
    media                   = Media()
    media.uuid              = media_uuid
    media.ownedby_oauth_sub = user_oauth_sub
    media.media_type        = media_type_enum.value
    media.title             = title[0]
    media.media_status      = MediaStatusEnum.Created.value
    db.session.add(media)
    db.session.commit()

    log.info(f"new upload created as media_uuid: <{media_uuid}> - <{user_oauth_sub}>")


    # then dispatch for media2hls through kafka
    msg_value = {
        "media_uuid": media_uuid,
        "oauth_sub":  user_oauth_sub
    }
    msg_value_json = json.dumps(msg_value)
    kproduce(encoded_msg_value=msg_value_json.encode("utf-8"))


    return {
        "status":              "success",
        "detected_media_type": media_type_enum.value,
        "url":                f"{os.environ["BACKEND_URL"]}/api/v1/media/{media_uuid}"
    }, 200




@blueprint.route("/api/v1/media", methods=["PUT"])
@jwt_required()
def edit_media_title():
    # verify ident
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    # parse req json body
    req_json = request.get_json(force=True, silent=True, cache=False)
    if not req_json:
        return { "status": "bad request" }, 400

    if "media_uuid" not in req_json:
        return { "status": "media_uuid not supplied" }, 400
    if "title" not in req_json:
        return { "status": "title not supplied" }, 400

    media_uuid = req_json["media_uuid"]
    new_title  = req_json["title"]

    new_title_filtered = title_filter(new_title)
    if not new_title_filtered[0]:
        return { "status": new_title_filtered[1] }, 422


    # exec query (match uuid and ownership)
    response = db.session.execute(db.update(Media).where(Media.uuid == media_uuid).where(Media.ownedby_oauth_sub == user_oauth_sub).values(title=new_title_filtered))
    if response.rowcount >= 1:
        db.session.commit()
        return { "status": "success" }, 200

    return { "status": "bad request" }, 400




@blueprint.route("/api/v1/media/<media_uuid>", methods=["DELETE"])
@jwt_required()
def delete_media():
    # verify ident
    jwt_oauth_sub  = get_jwt_identity()
    user_oauth_sub = db.session.execute(db.select(User.oauth_sub).where(User.oauth_sub == jwt_oauth_sub)).scalar_one_or_none()
    if not user_oauth_sub:
        return { "status": "invalid oauth identity" }, 401


    # parse req json body
    req_json = request.get_json(force=True, silent=True, cache=False)
    if not req_json:
        return { "status": "bad request" }, 400

    if "media_uuid" not in req_json:
        return { "status": "media_uuid not supplied" }, 400

    media_uuid = req_json["media_uuid"]

    # exec query (match uuid and ownership)
    response = db.session.execute(db.delete(Media).where(Media.uuid == media_uuid).where(Media.ownedby_oauth_sub == user_oauth_sub))
    if response.rowcount >= 1:
        db.session.commit()
        return { "status": "success" }, 200

    return { "status": "bad request" }, 400




@blueprint.route("/api/v1/media/<media_uuid>", methods=["GET"])
def get_media_info(media_uuid):
    media = db.session.execute(db.Select(Media).where(Media.uuid == media_uuid)).scalar_one_or_none()
    if media:
        uploader_display_name = db.session.execute(db.Select(User.display_name).where(User.oauth_sub == media.ownedby_oauth_sub)).scalar_one_or_none()
        return {
            "status":               media.media_status,
            "media_uuid":           media.uuid,
            "title":                media.title,
            "media_type":           media.media_type,
            "uploader_displayname": uploader_display_name,
            "vod_url":              f"{os.environ["BACKEND_URL"]}/api/v1/media/playback/{media_uuid}/playlist.m3u8"
        }, 200
    return { "status": "not found" }, 404




@blueprint.route("/api/v1/media/playback/<media_uuid>/<segment>", methods=["GET"])
def serve_hls(media_uuid, segment):
    media = db.session.execute(db.Select(Media).where(Media.uuid == media_uuid)).scalar_one_or_none()
    if media:
        # rig the vod transmission
        res = make_response(send_from_directory(f"{os.environ["UPLOAD_FOLDER"]}/{media.ownedby_oauth_sub}/{media.uuid}/", segment), 200)

        # don't trash the browser cache with video data
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        res.headers["Pragma"]  = "no-cache"
        res.headers["Expires"] = "0"

        return res

    return { "status": "not found" }, 404

