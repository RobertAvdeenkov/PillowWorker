from minio import Minio
import os
from upstash_blob import Bucket

bucker=Bucket.from_env()
cg=bucker.s3()
kwargs = cg.client_kwargs()

client = Minio(
    endpoint=kwargs["endpoint_url"].replace("https://", ""),
    access_key=kwargs["aws_access_key_id"],
    secret_key=kwargs["aws_secret_access_key"],
    secure=True
)
BUCKET='images'

def add_bucket():
    if not(client.bucket_exists(BUCKET)):
        client.make_bucket(BUCKET)
    