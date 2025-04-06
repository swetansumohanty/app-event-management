#!/bin/bash
# wait-for-it.sh

set -e

host="$1"
shift
cmd="$@"

echo "Waiting for MySQL to be ready..."
until mysqladmin ping -h"$host" -u"root" -p"root" --silent; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd 