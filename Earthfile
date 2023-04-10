VERSION 0.6
FROM alpine

pyright-validate:
    # renovate: datasource=pypi depName=pyright
    ARG PYRIGHT_VERSION=1.1.302
    # renovate: datasource=docker depName=python versioning=docker
    ARG PYTHON_VERSION=3.11
    FROM python:$PYTHON_VERSION
    WORKDIR /usr/src/app
    COPY . .
    RUN pip install -r requirements.txt -r requirements-dev.txt
    RUN pip install --no-cache-dir pyright==$PYRIGHT_VERSION
    RUN pyright

renovate-validate:
    # renovate: datasource=docker depName=renovate/renovate versioning=docker
    ARG RENOVATE_VERSION=34
    FROM renovate/renovate:$RENOVATE_VERSION
    WORKDIR /usr/src/app
    COPY renovate.json .
    RUN renovate-config-validator

lint:
    BUILD +pyright-validate
    BUILD +renovate-validate
