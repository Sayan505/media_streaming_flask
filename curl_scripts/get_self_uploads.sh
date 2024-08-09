source ./config

curl -X GET -v -H "Authorization: Bearer $token" "localhost:5000/api/v1/me/uploads?p=1&f=title"

