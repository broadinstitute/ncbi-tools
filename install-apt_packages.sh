#!/bin/bash

set -e -o pipefail

# Add some basics
apt-get update
apt-get install -y -qq --no-install-recommends \
	ca-certificates locales dirmngr \
	less nano vim git wget curl jq parallel \
	pigz zstd \
	python3 python3-pip python3-crcmod 

# Upgrade and clean
apt-get upgrade -y
apt-get clean

locale-gen en_US.UTF-8
