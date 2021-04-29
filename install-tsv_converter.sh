#!/bin/bash

set -e -o pipefail

REPO_COMMIT=54cfb5ab7182b9d7b399bca62f83490f0f32cddf

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
rm -f files/sample.tsv reports/sample-report.xml
cd -