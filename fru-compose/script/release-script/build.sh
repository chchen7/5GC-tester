#!/bin/bash

########################################################
# Script for building the docker image
#
# Usage:
#   ./build.sh <image tag>
#
# Description:
#   This script is used to build the docker image for free-ran-ue.
#   The image tag is the name of the image to be built, default is latest.
########################################################

LATEST_TAG="latest"
REPO_URL="https://github.com/free-ran-ue/free-ran-ue.git"
REPO_NAME="free-ran-ue"
IMAGE_NAME="alonza0314/free-ran-ue"

get_source_code() {
    if ! git clone $REPO_URL; then
        echo "Failed to clone the repository"
        return 1
    fi

    if [ "$image_tag" != "$LATEST_TAG" ]; then
        cd $REPO_NAME
        git checkout $image_tag
        cd ..
    fi
}

build_docker_image() {
    if ! docker build -f Dockerfile -t $IMAGE_NAME:$image_tag .; then
        echo "Failed to build the docker image"
        return 1
    fi
}

main() {
    local image_tag=${1:-$LATEST_TAG}

    if ! get_source_code $image_tag; then
        return 1
    fi

    if ! build_docker_image $image_tag; then
        return 1
    fi
}

main "$@"
