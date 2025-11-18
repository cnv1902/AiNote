import uuid
import requests
from typing import Tuple
from .config import settings


class S3Client:
    def __init__(self):
        self.base_url = settings.S3_ENDPOINT_URL.replace('/storage/v1/s3', '')
        self.bucket_name = settings.S3_BUCKET_NAME
        self.headers = {
            'Authorization': f'Bearer {settings.S3_SECRET_ACCESS_KEY}',
            'apikey': settings.S3_SECRET_ACCESS_KEY
        }

    def upload_image(self, file_data: bytes, filename: str, content_type: str = "image/jpeg") -> Tuple[str, str]:
        """
        Upload image to Supabase Storage and return the public URL and storage key
        Returns: (public_url, storage_key)
        """
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Upload to Supabase Storage
            upload_url = f"{self.base_url}/storage/v1/object/{self.bucket_name}/{unique_filename}"
            
            headers = self.headers.copy()
            headers['Content-Type'] = content_type
            
            response = requests.post(
                upload_url,
                data=file_data,
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Upload failed with status {response.status_code}: {response.text}")
            
            # Return the public URL
            public_url = f"{self.base_url}/storage/v1/object/public/{self.bucket_name}/{unique_filename}"
            return public_url, unique_filename
            
        except Exception as e:
            raise Exception(f"Failed to upload image to Supabase Storage: {str(e)}")

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
            delete_url = f"{self.base_url}/storage/v1/object/{self.bucket_name}/{storage_key}"
            
            response = requests.delete(
                delete_url,
                headers=self.headers
            )
            
            return response.status_code in [200, 204]
            
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


# Singleton instance
s3_client = S3Client()
