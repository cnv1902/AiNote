"""
Storage service for managing file uploads and deletions.
"""
import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Tuple

from app.core.config import settings


class StorageService:
    """Service for interacting with S3-compatible storage (Supabase)."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=boto3.session.Config(signature_version='s3v4')
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.base_url = settings.SUPABASE_URL if settings.SUPABASE_URL else settings.S3_ENDPOINT_URL.split('/storage/v1/s3')[0]

    def upload_image(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str = "image/jpeg"
    ) -> Tuple[str, str]:
        """
        Upload image to storage and return the public URL and storage key.
        
        Args:
            file_data: Binary image data
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            Tuple of (public_url, storage_key)
        """
        try:
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_data,
                ContentType=content_type
            )
            
            public_url = f"{self.base_url}/storage/v1/object/public/{self.bucket_name}/{unique_filename}"
            return public_url, unique_filename
            
        except ClientError as e:
            raise Exception(f"Failed to upload image: {str(e)}")

    def delete_image_by_key(self, storage_key: str) -> bool:
        """
        Delete image from storage using storage key.
        
        Args:
            storage_key: The unique key of the file in storage
            
        Returns:
            True if deletion was successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except Exception as e:
            print(f"Failed to delete image: {str(e)}")
            return False

    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from storage using the image URL.
        
        Args:
            image_url: The public URL of the image
            
        Returns:
            True if deletion was successful
        """
        try:
            if f"/object/public/{self.bucket_name}/" in image_url:
                key = image_url.split(f"/object/public/{self.bucket_name}/")[-1]
                return self.delete_image_by_key(key)
            return False
        except Exception as e:
            print(f"Failed to delete image: {str(e)}")
            return False


# Singleton instance
storage_service = StorageService()
