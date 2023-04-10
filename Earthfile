VERSION 0.6
FROM alpine

python-requirements:
    # renovate: datasource=docker depName=python versioning=docker
    ARG PYTHON_VERSION=3.11
    FROM python:$PYTHON_VERSION
    WORKDIR /usr/src/app
    COPY . .
    RUN pip install --no-cache-dir -r requirements.txt

python-dev-requirements:
    FROM +python-requirements
    WORKDIR /usr/src/app
    RUN pip install --no-cache-dir -r requirements-dev.txt

pre-commit-validate:
    # renovate: datasource=pypi depName=pre-commit
    ARG PRE_COMMIT_VERSION=2.21.0
    FROM +python-requirements
    WORKDIR /usr/src/app
    RUN pip install --no-cache-dir pre-commit==$PRE_COMMIT_VERSION
    RUN pre-commit run --all-files --show-diff-on-failure

pyright-validate:
    # renovate: datasource=pypi depName=pyright
    ARG PYRIGHT_VERSION=1.1.302
    FROM +python-dev-requirements
    WORKDIR /usr/src/app
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
    BUILD +pre-commit-validate
    BUILD +pyright-validate
    BUILD +renovate-validate
