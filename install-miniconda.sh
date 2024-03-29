#!/bin/bash
set -x -e -o pipefail

MINICONDA_VERSION="23.3.1"
MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-py38_${MINICONDA_VERSION}-0-Linux-x86_64.sh"

# download and run miniconda installer script
curl -sSL $MINICONDA_URL > "/tmp/Miniconda3-${MINICONDA_VERSION}-x86_64.sh"
chmod a+x "/tmp/Miniconda3-${MINICONDA_VERSION}-x86_64.sh"
/tmp/Miniconda3-${MINICONDA_VERSION}-x86_64.sh -b -f -p "$MINICONDA_PATH"
rm /tmp/Miniconda3-${MINICONDA_VERSION}-x86_64.sh

PATH="$MINICONDA_PATH/bin:$PATH"
hash -r
conda config --set always_yes yes --set changeps1 no
conda config --add channels r
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
#conda config --set channel_priority strict
conda config --set auto_update_conda false

conda clean -y --all

echo "$MINICONDA_PATH"
ls -lah $MINICONDA_PATH

