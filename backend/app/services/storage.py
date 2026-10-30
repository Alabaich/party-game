import uuid
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from ..config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4", retries={"max_attempts": 4}),
    region_name="auto",
)
# multipart for big videos, streamed from the temp file instead of RAM
_transfer = TransferConfig(multipart_threshold=16 * 1024 * 1024,
                           multipart_chunksize=16 * 1024 * 1024, max_concurrency=4)


def upload_file_to_r2(ext: str, content_type: str, fileobj) -> str:
    """Stream a file object to R2 and return its public URL."""
    key = f"{uuid.uuid4()}.{ext}"
    _s3.upload_fileobj(fileobj, settings.R2_BUCKET, key,
                       ExtraArgs={"ContentType": content_type}, Config=_transfer)
    return f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"
