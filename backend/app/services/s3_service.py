import boto3
from botocore.exceptions import ClientError
from app.config import settings

class S3Service:
    """
    Handles interactions with AWS S3 for storing and retrieving files.
    WHY: Centralizing AWS calls makes it easier to mock in tests or swap backends.
    """
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket = settings.S3_BUCKET_NAME

    def generate_presigned_upload_url(self, file_key: str, expiration=3600) -> str:
        """Generates a presigned URL for secure frontend uploads directly to S3."""
        try:
            response = self.s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': self.bucket,
                                                            'Key': file_key},
                                                    ExpiresIn=expiration)
            return response
        except ClientError as e:
            print(e)
            return ""

    def generate_presigned_download_url(self, file_key: str, expiration=3600) -> str:
        """Generates a presigned URL to download an object."""
        try:
            response = self.s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': self.bucket,
                                                            'Key': file_key},
                                                    ExpiresIn=expiration)
            return response
        except ClientError as e:
            print(e)
            return ""
            
    def download_file(self, file_key: str) -> bytes:
        """Downloads a file completely into memory."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error downloading {file_key}: {e}")
            raise

s3_service = S3Service()
