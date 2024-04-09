# 도커파일
FROM python:3.10-alpine
WORKDIR /chego

# 환경변수 설정
ENV DJANGO_SETTINGS_MODULE=chego_pjt.settings
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ASGI_MODULE=chego_pjt.asgi:application  

# 필요한 시스템 패키지 설치
RUN apk add --no-cache gcc musl-dev linux-headers mariadb-dev

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

EXPOSE 8000
COPY . .

# Daphne을 이용한 Django ASGI 애플리케이션 실행
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chego_pjt.asgi:application"]