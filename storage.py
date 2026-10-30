import boto3
from upstash_blob import Bucket

bucket = Bucket.from_env()
cfg = bucket.s3()
kwargs = cfg.client_kwargs()

s3 = boto3.client("s3", **kwargs)
