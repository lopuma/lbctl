#!/bin/bash
docker-compose run -e MY_USER -e BUCKET_NAME --rm --name lbctl-liburutegia lbctl-liburutegia "$@"