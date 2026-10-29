from minio import Minio
import os

client=Minio(os.getenv('ENDPOINT','localhost:9000'), access_key=os.getenv('ACCESS_KEY','minio'), secret_key=os.getenv('SECRET_KEY','minio123'),secure=False)

BUCKET='images'

def add_bucket():
    if not(client.bucket_exists(BUCKET)):
        client.make_bucket(BUCKET)
    