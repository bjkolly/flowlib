#!/usr/bin/env bash

# todo: Get tag from git tag else tag as latest

TAG="$1"
if [ -z "$TAG" ]; then
  TAG="latest"
fi

# Login to ECR
$(aws ecr get-login --no-include-email --region us-east-1)

docker build $(dirname $0) -t b23-flowlib:$TAG
docker tag b23-flowlib:$TAG 883886641571.dkr.ecr.us-east-1.amazonaws.com/b23-flowlib:$TAG
docker push 883886641571.dkr.ecr.us-east-1.amazonaws.com/b23-flowlib:$TAG
