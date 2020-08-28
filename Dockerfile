# FROM python:3.8.0
FROM joyzoursky/python-chromedriver:3.8

WORKDIR /opt
COPY . .

RUN pip install -r requirements.txt