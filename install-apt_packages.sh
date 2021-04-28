#!/bin/bash

set -e

# Add some basics
apt-get update
apt-get install -y -qq --no-install-recommends \
	ca-certificates locales dirmngr apt-utils \
	less nano vim git wget curl jq parallel \
	pigz zstd \
	python3 python3-pip python3-crcmod

# add source for node.js 14
set +e
curl -sL https://deb.nodesource.com/setup_14.x | bash -
set -e
apt-get install -y -qq --no-install-recommends \
	nodejs npm

# Upgrade and clean
#apt-get upgrade -y
apt-get clean

locale-gen en_US.UTF-8
