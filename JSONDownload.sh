#!/usr/bin/env bash

# Get the JSON file from TidePool.
# The token.txt file specifies the login credentials.
#
curl -v -X POST --netrc-file token.txt https://api.tidepool.org/auth/login >& tmp.txt

userid=$(cat tmp.txt | grep 'userid' | cut -d'"' -f14)
echo "My tidepool userid is (if empty, something failed): ${userid}"

token=$(cat tmp.txt | grep 'session\-token:' | cut -d' ' -f3)
# For some reason there is a ^M-style return carriage that needs to be removed.
token="${token//}"
echo "The web token is (if empty, something failed): ${token}"

curl -s -X GET -H "x-tidepool-session-token: ${token}" -H "Content-Type: application/json" "https://api.tidepool.org/data/${userid}" > ${1:-tmp.json}

# if it is not empty, move to download.json
[ -s tmp.json ] && mv tmp.json download.json
