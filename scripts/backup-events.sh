#!/bin/bash

set -euo pipefail

BOT_LOCATION=$HOME/operationbot
BACKUP_LOCATION=$BOT_LOCATION/backup

compare() {
  name="$1"

  echo "Checking $name"

  location="$BACKUP_LOCATION/$name"
  current_file="$BOT_LOCATION/database/$name.json"

  mkdir -p "$location"

  backup_date=$(date +%F-T%H-%M-%S)
  filename="$name.json-$backup_date.bak"
  new_file=$location/$filename

  if [ ! -e "$current_file" ]; then
    >&2 echo "no current file, nothing to do"
    return
  fi

  previous_file="$(find "$location" -name "$name.json*" | sort | tail -n 1)"
  if [ -z "$previous_file" ]; then
    echo "no previous file"
    no_previous=yes
  else
    current_sum=$(md5sum "$current_file" | cut -d' ' -f 1)
    previous_sum=$(gunzip -c "$previous_file" | md5sum - | cut -d' ' -f 1)

    echo "Current: $current_sum"
    echo "Previous: $previous_sum"
  fi

  if [ "${no_previous:-no}" = "yes" ] || [ "$current_sum" != "$previous_sum" ]; then
    echo "No match"
    cp "$current_file" "$new_file"
    gzip "$new_file"
  else
    echo "Match"
  fi
}


compare events
compare archive
