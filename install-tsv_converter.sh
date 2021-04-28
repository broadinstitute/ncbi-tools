#!/bin/bash

set -e -o pipefail

REPO_COMMIT=51bddbba58880ae4f6d5448e3ae7c722adfe84c4

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
cd -