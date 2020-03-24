#!/bin/bash
docker build -t $TRAVIS_REPO_SLUG .
echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USER" --password-stdin
docker push $TRAVIS_REPO_SLUG
