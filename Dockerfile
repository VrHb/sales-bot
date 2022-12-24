FROM python:3.8-slim

RUN mkdir -p /home/bot


ENV APP=/home/bot

WORKDIR $APP

COPY ./requirements.txt . 

RUN pip3 install --upgrade pip && pip3 install --no-cache-dir -r requirements.txt

COPY . $APP
