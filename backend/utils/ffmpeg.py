import os
import subprocess

from   config.logger import log


def media2hls(uploaded_file_path, output_folder, media_type, media_uuid):
    log.info(f" media2hls - media uuid <{media_uuid}> is currently being encoded ...")

    # set up output dir
    os.makedirs(output_folder, exist_ok=True)
    
    # config codecs
    vcodec_config = "-map 0:v:0? -preset fast -codec:v libx264 -crf 22" if media_type == "video" else ""
    acodec_config = "-map 0:a:0? -codec:a aac -b:a 128k -ac 2 -ar 48000"
    hls_config    = "-f hls -hls_time 10 -hls_playlist_type vod -hls_flags independent_segments"


    # encode to HLS!
    cmdstr = f"ffmpeg -y -i {uploaded_file_path} {vcodec_config} {acodec_config} {hls_config} {output_folder}/playlist.m3u8"
    proc   = subprocess.run(cmdstr, capture_output=True, shell=True)
    if proc.returncode != 0:
        log.error(f"media2hls - error - {proc.stderr}")
        return False

    return True

