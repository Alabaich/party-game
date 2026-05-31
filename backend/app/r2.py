import uuid
import boto3
from botocore.config import Config
from .config import settings

_s3 = boto3.client(
    "s3",
    endpoint_url=settings.r2_endpoint,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def make_presigned_put(filename: str, content_type: str) -> tuple[str, str]:
    """Повертає (upload_url, public_url).

    Фронт робить HTTP PUT на upload_url з тілом=файл і заголовком
    Content-Type рівним content_type. Після успіху медіа доступне за public_url.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    key = f"{uuid.uuid4()}.{ext}"

    upload_url = _s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=3600,
    )
    public_url = f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"
    return upload_url, public_url
