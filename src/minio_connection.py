from minio import Minio
from decouple import config

client = Minio(
        endpoint=config("MINIO_HOST")+':'+config("MINIO_PORT"),
        access_key=config("MINIO_USER"),
        secret_key=config("MINIO_PASSWORD"),
        secure= False,
        )