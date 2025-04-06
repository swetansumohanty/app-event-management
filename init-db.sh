#!/bin/bash
# init-db.sh

set -e

echo "Waiting for MySQL to be ready..."
until mysqladmin ping -h"$MYSQL_SERVER" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --silent; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

echo "Creating database tables..."
python -c "
from app.core.database import Base, engine
from app.vo.user import User
from app.vo.event import Event
from app.vo.attendee import Attendee

Base.metadata.create_all(bind=engine)
print('Database tables created successfully!')
" 