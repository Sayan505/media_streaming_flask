source ./config

curl -X PUT -v -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d '{"title":"new title, hello"}' localhost:5000/api/v1/media/$media_uuid

