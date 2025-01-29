# FROM nikolaik/python-nodejs:latest
FROM python:3.12
# FROM node:16-alpine

# set work directory
WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip

COPY ./UI/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./package /tmp/package/
RUN pip install /tmp/package

# RUN npm install

COPY /UI/backend /app

RUN rm -rf \
  /tmp/requirements.txt \
  /tmp/package