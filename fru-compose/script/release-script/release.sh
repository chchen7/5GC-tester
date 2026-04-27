#!/bin/bash

########################################################
# Script for releasing the docker image
#
# Usage:
#   ./release.sh <image tag>
#
# Description:
#   This script is used to release the docker image for free-ran-ue.
#   The image tag is the tag of the image to be released, default is latest.
########################################################

IMAGE_NAME="alonza0314/free-ran-ue"
IMAGE_LATEST_TAG="latest"

push_version_tag_image() {
    if ! docker push $IMAGE_NAME:$image_tag; then
        echo "Failed to push the version tag image"
        return 1
    fi

    echo "Successfully pushed the image with tag $image_tag"
}

push_latest_tag_image() {
    if ! docker tag $IMAGE_NAME:$image_tag $IMAGE_NAME:$IMAGE_LATEST_TAG; then
        echo "Failed to tag the version tag image"
        return 1
    fi

    if ! docker push $IMAGE_NAME:$IMAGE_LATEST_TAG; then
        echo "Failed to push the latest tag image"
        return 1
    fi

    echo "Successfully pushed the latest tag image"
}

main() {
    local image_tag=${1:-$IMAGE_TAG}

    if ! push_version_tag_image $image_tag; then
        return 1
    fi

    if ! push_latest_tag_image $image_tag; then
        return 1
    fi
}

main "$@"
