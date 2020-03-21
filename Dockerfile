FROM python:alpine

ENV FLASK_APP react-ocd.py
ENV FLASK_ENV development

COPY server/ /back-end/

WORKDIR /back-end/

RUN apk add build-base &&\
    pip install -r requirements.txt

EXPOSE 5000

CMD flask run --host=0.0.0.0

