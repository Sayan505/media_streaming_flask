import subprocess
import json

from   models.upload_model import MediaTypeEnum


def get_media_type(uploaded_file_path):
    try:
        cmdstr = f"ffprobe -print_format json -v quiet -show_format -show_streams {uploaded_file_path}"
        proc   = subprocess.run(cmdstr, capture_output=True, shell=True, timeout=3)
        if proc.returncode != 0:
            return None

        probe   = json.loads(proc.stdout.decode("utf-8"))

        streams = probe["streams"]
        if len(streams) < 1:
            return None


        has_audio = any(stream["codec_type"]  == "audio" for stream in streams)
        has_video = any((stream["codec_type"] == "video" and stream["avg_frame_rate"] != "0/0") for stream in streams)  # ignore thumbnails embedded in audio files

        if has_video: return MediaTypeEnum.Video
        if has_audio: return MediaTypeEnum.Audio
        
        return None


    except subprocess.TimeoutExpired:
        return None

