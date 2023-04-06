#!/bin/bash
#docker run -it -v /var/run/docker.sock:/var/run/docker.sock lbctl-container "$@"
# docker run -it --rm -v /home/lopuma/${COVER_DIR}:/app/covers-prueba lbctl-container "$@"
docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia "$@"
