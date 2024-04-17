# 도커파일
# FROM python:3.10-alpine
# FROM cloudtype/python:3.11
# WORKDIR /chego

# # 환경변수 설정
# ENV DJANGO_SETTINGS_MODULE=chego_pjt.settings
# ENV PYTHONUNBUFFERED=1
# ENV DJANGO_ASGI_MODULE=chego_pjt.asgi:application  

# # 필요한 시스템 패키지 설치
# RUN apk add --no-cache gcc musl-dev linux-headers mariadb-dev

# COPY requirements.txt requirements.txt
# RUN pip install -r requirements.txt

# EXPOSE 8000
# COPY . .

# # Daphne을 이용한 Django ASGI 애플리케이션 실행
# CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chego_pjt.asgi:application"]

FROM cloudtype/python:3.11
# FROM python:3.10-alpine


RUN apt-get update -y
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev pkg-config libc6-dev linux-headers-generic sudo nfs-kernel-server\
    && rm -rf /var/lib/apt/lists/*

# 도커설치
RUN curl -fsSL https://get.docker.com/ -o get-docker.sh && \
    sh get-docker.sh

WORKDIR /chego

ENV DJANGO_SETTINGS_MODULE=chego_pjt.settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ASGI_MODULE=chego_pjt.asgi:application  

COPY ./requirements.txt* ./
# RUN pip install gunicorn
RUN pip install -r requirements.txt
# RUN groupadd -r python && useradd -r -g python python

EXPOSE 8000

COPY --chown=python:python ./ ./
# RUN chown -f python:python /chego && rm -rf .git*
RUN chown -f python:python /chego




USER python

# CMD python3 manage.py makemigrations && python3 manage.py migrate && python3 manage.py runserver 0:8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "chego_pjt.asgi:application"]