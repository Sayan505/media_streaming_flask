import os
import subprocess

from   config.logger import log

from   models.upload_model import MediaTypeEnum


def media2hls(uploaded_file_path, output_folder, media_type, media_uuid):
    log.info(f" media2hls - media uuid <{media_uuid}> is currently being encoded ...")

    # set up output dir
    os.makedirs(output_folder, exist_ok=True)


    # config codecs for adaptive-bitrate video streaming
    cfgstr = ""
    if media_type == MediaTypeEnum.Video.value:
        cfgstr = (f"-map 0:v:0 -map 0:a:0 -map 0:v:0 -map 0:a:0 -map 0:v:0 -map 0:a:0 "          \
                  f"-c:v libx264 -crf 22 -c:a aac -ar 48000 "                                    \
                  f"-maxrate:v:0 1000k -b:a:0 64k  "                                             \
                  f"-maxrate:v:1 2000k -b:a:1 128k "                                             \
                  f"-maxrate:v:2 5000k -b:a:2 256k "                                             \
                  f'-var_stream_map "v:0,a:0,name:low v:1,a:1,name:med v:2,a:2,name:high" '      \
                  f"-f hls -hls_playlist_type vod -hls_time 10 -hls_flags independent_segments " \
                  f"-master_pl_name playlist.m3u8 "                                              \
                  f"-hls_segment_filename {os.path.join(output_folder, "segment-%v-%04d.ts")} "  \
                  f"{os.path.join(output_folder, "playlist-%v.m3u8")} ")
    elif media_type == MediaTypeEnum.Audio.value:
        cfgstr = (f"-map 0:a:0 -c:a aac -b:a 256k -ar 48000 "                                    \
                  f"-f hls -hls_time 10 -hls_playlist_type vod -hls_flags independent_segments " \
                  f"-hls_segment_filename {os.path.join(output_folder, "segment-%04d.ts")} "     \
                  f"{os.path.join(output_folder, "playlist.m3u8")} ")
    elif media_type == MediaTypeEnum.VideoNoSound.value:
        cfgstr = (f"-map 0:v:0 -map 0:v:0 -map 0:v:0 "                                           \
                  f"-c:v libx264 -crf 22 "                                                       \
                  f"-maxrate:v:0 1000k "                                                         \
                  f"-maxrate:v:1 2000k "                                                         \
                  f"-maxrate:v:2 5000k "                                                         \
                  f'-var_stream_map "v:0,name:low v:1,name:med v:2,name:high" '                  \
                  f"-f hls -hls_playlist_type vod -hls_time 10 -hls_flags independent_segments " \
                  f"-master_pl_name playlist.m3u8 "                                              \
                  f"-hls_segment_filename {os.path.join(output_folder, "segment-%v-%04d.ts")} "  \
                  f"{os.path.join(output_folder, "playlist-%v.m3u8")} ")
    else:
        log.error(f"media2hls - error - invalid media_type {media_type}")
        return False


    # encode to HLS!
    cmdstr = f"ffmpeg -y -i {uploaded_file_path} {cfgstr}"
    proc   = subprocess.run(cmdstr, capture_output=True, shell=True)
    if proc.returncode != 0:
        log.error(f"media2hls - error - stderr: {proc.stderr}    cmdstr: {cmdstr}")
        return False

    return True

