#!/bin/bash
# purpose: automatically upload plugins from Github.com
#          under FNNDSC with the tag "chris-app" to chrisstore.co
# dependencies: jq curl parallel
# usage:
#
#     env CHRIS_STORE_URL=https://chrisstore.co/api/v1/ CHRIS_STORE_USER=chris:chris1234 ./upload_all_from_github.sh 8
#
# positional argument:
#
#     J   number of concurrent jobs
#
# future work: max 100 plugins, gotta use pagination after that

org='FNNDSC'
search="topic:chris-app+org:$org"

source_dir=$(dirname "$(readlink -f "$0")")

list=$(
  curl -s "https://api.github.com/search/repositories?per_page=100&q=$search" \
    -H 'accept:application/vnd.github.v3+json' \
    | jq -r '.items[] | .full_name' 
)


if [ -n "$1" ]; then
  parallel -j $1 $source_dir/upload_one_from_github.sh {} <<< $list
else
  for repo in $list; do
    $source_dir/upload_one_from_github.sh $repo
  done
fi
