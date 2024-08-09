source ./config

curl -X GET -v -H "Authorization: Bearer $token" "localhost:5000/api/v1/search/me?q=title&p=0"

