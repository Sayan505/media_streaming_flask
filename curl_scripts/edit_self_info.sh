source ./config

curl -X PUT -v -H "Authorization: Bearer $token" -H "Content-Type: application/json" -d '{"display_name":"Sayan"}' localhost:5000/api/v1/me

