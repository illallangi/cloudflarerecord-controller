# Main image
FROM docker.io/library/python:3.10.3

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    XDG_CONFIG_HOME=/config

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN python -m pip install -r requirements.txt

ADD . /usr/src/app
RUN python -m pip install --use-feature=in-tree-build .

CMD kopf run --liveness=http://0.0.0.0:8080/healthz -m cloudflarerecord-controller

ARG VCS_REF
ARG VERSION
ARG BUILD_DATE
LABEL maintainer="Andrew Cole <andrew.cole@illallangi.com>" \
      org.label-schema.build-date=${BUILD_DATE} \
      org.label-schema.description="TODO: Specify Description" \
      org.label-schema.name="cloudflarerecord-controller" \
      org.label-schema.schema-version="1.0" \
      org.label-schema.url="http://github.com/illallangi/cloudflarerecord-controller" \
      org.label-schema.usage="https://github.com/illallangi/cloudflarerecord-controller/blob/master/README.md" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/illallangi/cloudflarerecord-controller" \
      org.label-schema.vendor="Illallangi Enterprises" \
      org.label-schema.version=$VERSION