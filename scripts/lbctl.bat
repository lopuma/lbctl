@echo off
@set "COMPOSE_FILE=D:\Development\Liburutegia\docker-compose.yml"
@docker-compose run --rm --name lbctl-liburutegia lbctl-liburutegia %*