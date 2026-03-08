#!/bin/bash
export OPERATIVE_BUILDKIT_ADDR="tcp://buildkitd.os-stogops-sbx.svc.cluster.local:1234"
export OPERATIVE_CONTAINER_REPO="us-central1-docker.pkg.dev/operative-001/os-stogops/os/stogops"

/workspace/task-tracker/bin/buildctl --addr "$OPERATIVE_BUILDKIT_ADDR" build \
  --progress=plain --no-cache \
  --frontend dockerfile.v0 \
  --local context=/workspace/real-track \
  --local dockerfile=/workspace/real-track \
  --opt filename=Dockerfile \
  --output type=image,name="$OPERATIVE_CONTAINER_REPO/real-track:latest",push=true
