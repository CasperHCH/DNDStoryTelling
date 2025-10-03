#!/usr/bin/env bash
#   Use this script to test if a given TCP host/port are available

TIMEOUT=15

while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout=*)
      TIMEOUT="${1#*=}"
      ;;
    *)
      HOST_PORT="$1"
      ;;
  esac
  shift

done

HOST=$(echo $HOST_PORT | cut -d: -f1)
PORT=$(echo $HOST_PORT | cut -d: -f2)

echo "Waiting for $HOST:$PORT to be ready..."
echo "Timeout set to $TIMEOUT seconds."

for i in $(seq $TIMEOUT); do
  nc -z $HOST $PORT && exit 0
  sleep 1
done

exit 1