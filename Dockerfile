FROM python:3.7-alpine

ADD docs/ /docs
ADD entrypoint.py /

RUN adduser -u 2004 -D docker &&\
    pip install cfn-lint

ENTRYPOINT ["/entrypoint.py"]
