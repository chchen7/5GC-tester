SHELL := /bin/bash

IMAGE_NAME = docker_open5gs
BUILD_PATH = base

.PHONY: build

build:
	set -a; \
	source .env; \
	set +a; \
	cd $(BUILD_PATH) && docker build -t $(IMAGE_NAME) .