# pull official base image
FROM python:3.12

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

COPY /UI/backend /app

RUN rm -rf \
  /tmp/requirements.txt \
  /tmp/package

# Create a default .env file if it doesn't exist
RUN touch .env && \
  echo "# Default environment variables" >> .env && \
  echo "DEBUG=False" >> .env