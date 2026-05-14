#!/bin/bash

set -e -o pipefail

wget -q "https://github.com/Asymmetrik/broad-tsv-converter/archive/$ASYMMETRIK_REPO_COMMIT.tar.gz"
mkdir -p /opt/converter
tar -xf "$ASYMMETRIK_REPO_COMMIT.tar.gz" -C /opt/converter --strip-components=1

cd /opt/converter
mkdir -p logs staging

# Inject npm overrides to pull CVE-free transitive deps (issue #20).
# The upstream package.json (commit pinned in the Dockerfile) is from 2018 and
# pulls vulnerable versions of tar, glob, serialize-javascript, and ssh2.
jq '. + {overrides: {
  "tar": ">=7.5.7",
  "glob": ">=10.5.0",
  "serialize-javascript": ">=7.0.3",
  "ssh2": ">=1.4.0",
  "minimatch": ">=3.1.4"
}}' package.json > package.json.new && mv package.json.new package.json

npm install
rm -rf files/sample.tsv reports/sample-report.xml files/tests reports/tests
cd -

# Remove the npm CLI now that the converter is installed (issue #20).
# npm itself bundles vulnerable copies of tar/glob/minimatch/etc. The converter
# runtime only needs `node`, not `npm`/`npx`/`corepack`. Deleting these here
# (in the same RUN layer as the install) keeps them out of the final image.
rm -rf /opt/conda/lib/node_modules/npm \
       /opt/conda/lib/node_modules/corepack \
       /opt/conda/bin/npm \
       /opt/conda/bin/npx \
       /opt/conda/bin/corepack