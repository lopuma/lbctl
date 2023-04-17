#!/bin/bash
##export MY_USER="lopuma" 
##export BUCKET_NAME="covers-liburutegia" 
docker-compose run -e MY_USER -e BUCKET_NAME --rm --name lbctl-liburutegia lbctl-liburutegia "$@"