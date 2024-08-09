# USAGE EXAMPLES
### POST /api/v1/media
```console
$ curl -X POST -H "Authorization: Bearer $token" -F file=@'./video.mp4' -F title="A New Upload" "localhost:5000/api/v1/media"

{
  "status": "success",
  "detected_media_type": "video",
  "url": "http://localhost:5000/api/v1/media/252103b7-6971-4b48-a1ef-699396d2d9ac"
}
```

### GET /api/v1/media/<media_uuid>
```console
$ curl -X GET "localhost:5000/api/v1/media/$media_uuid"

{
  "status": "ready",
  "media_uuid": "252103b7-6971-4b48-a1ef-699396d2d9ac",
  "title": "A New Upload",
  "media_type": "video",
  "uploader_display_name": "Sayan",
  "upload_date": "Fri, 09 Aug 2024 18:36:07 GMT",
  "vod_url": "http://localhost:5000/api/v1/media/playback/252103b7-6971-4b48-a1ef-699396d2d9ac/playlist.m3u8"
}

$ # for playback:
$ # http://localhost:3000/play?m=<media_uuid>  # on the frontend
$ # or paste the vod_url (playlist) into any HLS supported media player such as VLC
```

### GET /api/v1/search?q="search_term"&p=page_num
```console
$ curl -X GET "localhost:5000/api/v1/search?q=upload&p=0"

$ # uses Elasticsearch (paginated)
{
  "current_page": 0,
  "npages": 1,
  "nhits": 3,
  "hits": [
    {
      "_index": "all_media_uploads",
      "_id": "91",
      "_score": 0.26706278,
      "_source": {
        "media_title": "A New Upload",
        "media_uuid": "252103b7-6971-4b48-a1ef-699396d2d9ac",
        "media_type": "video"
      }
    },
    # <remaining results truncated for this example>
  ]
}
```

### Other Routes:
- GET /api/login (oauth route)
- GET /api/auth (oauth callback)
- DELETE /api/v1/media/<media_uuid>
- PUT /api/v1/media/<media_uuid>
- GET /api/v1/me
- PUT /api/v1/me
- GET /api/v1/me/uploads?p=page_num&f="filter_string"
- GET /api/v1/search/me?q="search_term"&p=page_num
