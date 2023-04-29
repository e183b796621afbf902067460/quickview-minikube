FROM python:3.10-slim

USER root
RUN apt-get update && apt-get install -y git

WORKDIR /opt/dagster/app
ENV DAGSTER_HOME=/opt/dagster/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY etl ./etl

COPY workspace.yaml ./
COPY dagster.yaml ./
COPY celery.yaml ./

RUN pip install git+https://github.com/e183b796621afbf902067460/c3d3-framework.git#egg=c3d3
