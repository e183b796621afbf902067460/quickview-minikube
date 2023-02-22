FROM python:3.10-slim

USER root
RUN apt-get update && apt-get install -y git

WORKDIR /opt/dagster/app
ENV DAGSTER_HOME=/opt/dagster/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY dagster.yaml ./
COPY workspace.yaml ./
COPY c3d3 ./c3d3

RUN pip install git+https://github.com/e183b796621afbf902067460/raffaelo.git#egg=raffaelo
RUN pip install git+https://github.com/e183b796621afbf902067460/medici.git#egg=medici
RUN pip install git+https://github.com/e183b796621afbf902067460/d3f1nance.git#egg=d3f1nance
RUN pip install git+https://github.com/e183b796621afbf902067460/c3f1nance.git#egg=c3f1nance
RUN pip install git+https://github.com/e183b796621afbf902067460/d3tl.git#egg=d3tl
RUN pip install git+https://github.com/e183b796621afbf902067460/c3tl.git#egg=c3tl
RUN pip install git+https://github.com/e183b796621afbf902067460/trad3r.git#egg=trad3r
