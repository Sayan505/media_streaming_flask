source ./config

curl -X POST -v -H "Authorization: Bearer $token" -F file=@'./video.mp4' -F title="A New Upload | this is its title" localhost:5000/api/v1/media

