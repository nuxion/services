#!/bin/sh
set -e
API_VERSION=${1:-v1}
POETRY_VERSION=`python scripts/get_version.py`
PKG_NAME=services

cat <<EOT > ${PKG_NAME}/__version__.py
__version__ = "${POETRY_VERSION}"
EOT
