#!/bin/sh
BACKUP_LOCATION=$HOME/tmp/unique
CURRENT_LOCATION=$HOME/tmp/sort

current_filename=$(ls $CURRENT_LOCATION -1 | head -n 1)
current_file=$CURRENT_LOCATION/$current_filename

filename=$current_filename
new_file=$BACKUP_LOCATION/$filename

previous_file=$BACKUP_LOCATION/$(ls $BACKUP_LOCATION -1 | tail -n 1)

current_sum=$(md5sum $current_file | cut -d' ' -f 1)
previous_sum=$(md5sum $previous_file | cut -d' ' -f 1)

echo -n "Current: "
echo $current_sum
echo -n "Previous: "
echo $previous_sum

if [ $current_sum != $previous_sum ]; then
  echo "No match"
  mv $current_file $new_file
else
  echo "Match"
  rm $current_file
fi

#cp ~/operationbot/eventDatabase.json ~/operationbot/backup/eventDatabase.json-$(date +\%F-T\%H-\%M-\%S).bak


