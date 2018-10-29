FROM python:3.7-alpine

LABEL cfn.version="0.8.2" tool.version="2018.1.1" release.date="2018.10.28"

ADD docs/ /docs
ADD entrypoint.py /

RUN adduser -u 2004 -D docker &&\
  pip install cfn-lint &&\
  rm -rvf /root/.cache &&\
  chown -Rv docker:docker /docs entrypoint.py

ENTRYPOINT ["/entrypoint.py"]
