import os
import shutil
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


if settings.USE_OBJECT_STORAGE:
    _session = boto3.session.Session()
    _s3_client = _session.client(
        's3',
        endpoint_url=settings.IONOS_ENDPOINT_URL or None,
        aws_access_key_id=settings.IONOS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.IONOS_SECRET_ACCESS_KEY or None,
    )
    BUCKET = settings.IONOS_BUCKET_NAME


def upload_file(local_path: str, object_name: str) -> str:
    """Upload a local file and return the object key or path."""
    if settings.USE_OBJECT_STORAGE:
        try:
            _s3_client.upload_file(local_path, BUCKET, object_name)
            return object_name
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error uploading {local_path} to object storage: {e}")
            raise
    else:
        # For local storage just keep the file and return its path
        return local_path


def download_file(object_name: str, local_path: str) -> None:
    """Download an object to the given local path."""
    if settings.USE_OBJECT_STORAGE:
        try:
            _s3_client.download_file(BUCKET, object_name, local_path)
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error downloading {object_name} from object storage: {e}")
            raise
    else:
        shutil.copyfile(object_name, local_path)


def delete_object(object_name: str) -> None:
    """Delete an object from storage."""
    if settings.USE_OBJECT_STORAGE:
        try:
            _s3_client.delete_object(Bucket=BUCKET, Key=object_name)
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error deleting {object_name} from object storage: {e}")
    else:
        if os.path.exists(object_name):
            os.remove(object_name)


def generate_presigned_url(object_name: str, expiration: int = 3600) -> str:
    """Generate a URL for downloading the stored object."""
    if settings.USE_OBJECT_STORAGE:
        try:
            return _s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': BUCKET, 'Key': object_name},
                ExpiresIn=expiration,
            )
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error generating URL for {object_name}: {e}")
            raise
    else:
        return object_name
