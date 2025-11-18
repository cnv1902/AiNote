import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Tuple
from .config import settings


class SupabaseStorageClient:
    def __init__(self):
        # Use S3 protocol with boto3
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=boto3.session.Config(signature_version='s3v4')
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.base_url = settings.SUPABASE_URL if settings.SUPABASE_URL else "https://xzaqljbaicgcuiuwrmrs.supabase.co"

    def upload_image(self, file_data: bytes, filename: str, content_type: str = "image/jpeg") -> Tuple[str, str]:
        """
        Upload image to Supabase Storage via S3 protocol and return the public URL and storage key
        Returns: (public_url, storage_key)
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Upload via S3 protocol
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_data,
                ContentType=content_type
            )
            
            # Return the public URL
            public_url = f"{self.base_url}/storage/v1/object/public/{self.bucket_name}/{unique_filename}"
            return public_url, unique_filename
            
        except ClientError as e:
            raise Exception(f"Failed to upload image to Supabase Storage: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to upload image: {str(e)}")

    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from Supabase Storage using the image URL
        """
        try:
            # Extract the key from URL
            if f"/object/public/{self.bucket_name}/" in image_url:
                key = image_url.split(f"/object/public/{self.bucket_name}/")[-1]
                return self.delete_image_by_key(key)
            return False
            
        except Exception as e:
            print(f"Failed to delete image: {str(e)}")
            return False

    def delete_image_by_key(self, storage_key: str) -> bool:
        """
        Delete image from Supabase Storage using storage key
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
            
        except ClientError as e:
            print(f"Failed to delete image: {str(e)}")
            return False
        except Exception as e:
            print(f"Failed to delete image: {str(e)}")
            return False

    def delete_multiple_images(self, image_urls: list[str]) -> int:
        """
        Delete multiple images from Supabase Storage
        Returns the count of successfully deleted images
        """
        deleted_count = 0
        for url in image_urls:
            if self.delete_image(url):
                deleted_count += 1
        return deleted_count


# Singleton instance - backward compatibility
s3_client = SupabaseStorageClient()
