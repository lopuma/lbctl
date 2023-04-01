#!/bin/bash
#docker run -it -v /var/run/docker.sock:/var/run/docker.sock lbctl-container "$@"
docker run -it -v ./covers:/app/covers lbctl-container "$@"
