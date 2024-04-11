#!/bin/sh

# 데이터베이스 마이그레이션 실행
python3 manage.py makemigrations
python3 manage.py migrate

# 원래 실행하려던 커맨드 실행
exec "$@"