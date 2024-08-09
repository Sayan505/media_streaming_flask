source ./config

curl -X DELETE -v -H "Authorization: Bearer $token" localhost:5000/api/v1/media/$media_uuid

