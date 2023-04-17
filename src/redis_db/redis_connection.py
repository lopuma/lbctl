import redis
from decouple import config

r = redis.Redis(host=config("REDIS_HOST"), port=6379, password=config("REDIS_PASSWORD"))