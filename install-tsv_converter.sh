#!/bin/bash

set -e -o pipefail

REPO_COMMIT=c226ebd14ff52e49538228e66b045df483360f1a

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
rm -f files/sample.tsv reports/sample-report.xml
cd -