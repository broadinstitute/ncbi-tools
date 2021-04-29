#!/bin/bash
set -e

apt-get update

apt-get install -y -qq --no-install-recommends \
	ca-certificates locales locales-all dirmngr apt-utils \
	less nano vim git wget curl jq parallel \
	pigz zstd \
	python3 python3-pip python3-crcmod

apt-get clean

locale-gen en_US.UTF-8
