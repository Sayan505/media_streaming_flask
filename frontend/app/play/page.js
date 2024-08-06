'use client'

import { useState, useEffect, useRef } from "react";
import { useSearchParams   } from "next/navigation";

import Hls from "hls.js";

import axios_client from "../../axios_instance.js";


export default function Play() {
    const searchParams = useSearchParams();
    const media_uuid   = searchParams.get("m");

    const [media_info, set_media_info] = useState(false);

    const videoRef = useRef(null);

    useEffect(() => {
        axios_client.get(`/api/v1/media/${media_uuid}`).then((res) => {
            set_media_info(res.data);

            if(Hls.isSupported()) {
                var hls = new Hls();

                hls.loadSource(res.data.vod_url);
                hls.attachMedia(videoRef.current);
                
                hls.on(Hls.Events.MEDIA_ATTACHED, () => {
                    videoRef.current.play();
                });
            } else if(videoRef.current.canPlayType("application/vnd.apple.mpegurl")) {
                videoRef.current.src = res.vod_url;
                videoRef.current.addEventListener("canplay", () => {
                    videoRef.current.play();
                });
            }
        });
    }, []);


    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-12">
            <div>
                <div className="inline size-96 break-all"> title: {media_info.title} - {media_info.uploader_display_name} </div>
                <br/>
                <div className="inline size-96 break-all"> media_type: {media_info.media_type} </div>
                <br/>
                <div className="inline size-96 break-all"> media_uuid: {media_info.media_uuid} [{media_info.status}] </div>
                <br/>
                <div className="inline size-96 break-all"> vod_url: {media_info.vod_url} </div>
                <br/><br/>
                <video ref={videoRef} controls style={{ width: "1280px", height: "720px" }}/>
            </div>
        </main>
    );
}

