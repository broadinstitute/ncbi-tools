#!/bin/bash

set -e -o pipefail

# Silence some warnings about Readline. Checkout more over her
# https://github.com/phusion/baseimage-docker/issues/58
DEBIAN_FRONTEND=noninteractive
echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# Add some basics
apt-get update
apt-get install -y -qq --no-install-recommends \
	ca-certificates wget curl \
	python-crcmod locales \
	dirmngr \
	pigz zstd

# Upgrade and clean
apt-get upgrade -y
apt-get clean

locale-gen en_US.UTF-8
