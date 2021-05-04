#!/bin/bash

set -e -o pipefail

REPO_COMMIT=c1140b3f9106dc9a4cd1f354ae08cac68796a0dd

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
rm -f files/sample.tsv reports/sample-report.xml
cd -