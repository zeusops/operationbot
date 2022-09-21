#!/bin/sh

#set -x
#set -e

BOT_LOCATION=$HOME/operationbot
BACKUP_LOCATION=$BOT_LOCATION/backup

current_file=$BOT_LOCATION/database/events.json

backup_date=$(date +\%F-T\%H-\%M-\%S)
filename=events/events.json-$backup_date.bak
new_file=$BACKUP_LOCATION/$filename

previous_file=$(ls $BACKUP_LOCATION/events/events.json* -1 | tail -n 1)

current_sum=$(md5sum $current_file | cut -d' ' -f 1)
previous_sum=$(gunzip -c $previous_file | md5sum - | cut -d' ' -f 1)

echo -n "Current: "
echo $current_sum
echo -n "Previous: "
echo $previous_sum

if [ $current_sum != $previous_sum ]; then
  echo "No match"
  cp $current_file $new_file
  gzip $new_file
else
  echo "Match"
fi


current_file=$BOT_LOCATION/database/archive.json

backup_date=$(date +\%F-T\%H-\%M-\%S)
filename=archive/archive.json-$backup_date.bak
new_file=$BACKUP_LOCATION/$filename

previous_file=$(ls $BACKUP_LOCATION/archive/archive.json* -1 | tail -n 1)

current_sum=$(md5sum $current_file | cut -d' ' -f 1)
previous_sum=$(gunzip -c $previous_file | md5sum - | cut -d' ' -f 1)

echo -n "Current: "
echo $current_sum
echo -n "Previous: "
echo $previous_sum

if [ $current_sum != $previous_sum ]; then
  echo "No match"
  cp $current_file $new_file
  gzip $new_file
else
  echo "Match"
fi
#cp ~/operationbot/eventDatabase.json ~/operationbot/backup/eventDatabase.json-$(date +\%F-T\%H-\%M-\%S).bak


