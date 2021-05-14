#!/bin/bash

set -e -o pipefail

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$ASYMMETRIK_REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$ASYMMETRIK_REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging
npm install
rm -rf files/sample.tsv reports/sample-report.xml files/tests reports/tests
cd -