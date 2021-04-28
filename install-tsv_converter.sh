#!/bin/bash

set -e -o pipefail

REPO_COMMIT=b5a593cd403b9bcbf288f9714c04337ea31c3010

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
cd -