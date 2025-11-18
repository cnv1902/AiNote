"""
Dịch vụ lưu trữ để quản lý tải lên và xóa file.
"""
import uuid
import boto3
from botocore.exceptions import ClientError
from typing import Tuple

from app.core.config import settings


class StorageService:
    """Dịch vụ để tương tác với lưu trữ tương thích S3 (Supabase)."""
    
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
        Tải hình ảnh lên kho lưu trữ và trả về URL công khai và storage key.
        
        Args:
            file_data: Dữ liệu hình ảnh nhị phân
            filename: Tên file gốc
            content_type: Loại MIME của file
            
        Returns:
            Tuple của (public_url, storage_key)
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
            raise Exception(f"Tải lên hình ảnh thất bại: {str(e)}")

    def delete_image_by_key(self, storage_key: str) -> bool:
        """
        Xóa hình ảnh từ kho lưu trữ bằng storage key.
        
        Args:
            storage_key: Khóa duy nhất của file trong kho lưu trữ
            
        Returns:
            True nếu xóa thành công
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_key
            )
            return True
        except Exception as e:
            print(f"Không thể xóa hình ảnh: {str(e)}")
            return False

    def delete_image(self, image_url: str) -> bool:
        """
        Xóa hình ảnh từ kho lưu trữ bằng URL hình ảnh.
        
        Args:
            image_url: URL công khai của hình ảnh
            
        Returns:
            True nếu xóa thành công
        """
        try:
            if f"/object/public/{self.bucket_name}/" in image_url:
                key = image_url.split(f"/object/public/{self.bucket_name}/")[-1]
                return self.delete_image_by_key(key)
            return False
        except Exception as e:
            print(f"Không thể xóa hình ảnh: {str(e)}")
            return False


# Instance singleton
storage_service = StorageService()
