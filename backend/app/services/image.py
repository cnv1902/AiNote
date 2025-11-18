"""
Dịch vụ xử lý hình ảnh để trích xuất siêu dữ liệu và dữ liệu EXIF.
"""
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


class ImageService:
    """Dịch vụ xử lý hình ảnh và trích xuất siêu dữ liệu."""
    
    @staticmethod
    def extract_exif_data(image_data: bytes) -> Dict[str, Any]:
        """
        Trích xuất dữ liệu EXIF từ hình ảnh.
        
        Args:
            image_data: Dữ liệu hình ảnh nhị phân
            
        Returns:
            Dictionary chứa dữ liệu EXIF
        """
        try:
            image = Image.open(BytesIO(image_data))
            exif_data = {}
            
            exif_data['width'] = image.width
            exif_data['height'] = image.height
            exif_data['format'] = image.format

            exif = image.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
            
            return exif_data
        except Exception as e:
            print(f"Lỗi khi trích xuất EXIF: {str(e)}")
            return {}

    @staticmethod
    def parse_metadata(exif_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phân tích dữ liệu EXIF thành siêu dữ liệu có cấu trúc.
        
        Args:
            exif_data: Dictionary dữ liệu EXIF thô
            
        Returns:
            Dictionary siêu dữ liệu có cấu trúc
        """
        metadata = {
            'width': exif_data.get('width'),
            'height': exif_data.get('height'),
            'camera_make': exif_data.get('Make'),
            'camera_model': exif_data.get('Model'),
            'orientation': exif_data.get('Orientation'),
            'datetime_original': None,
            'gps_latitude': None,
            'gps_longitude': None,
            'extra': {}
        }
        
        # Phân tích datetime
        datetime_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
        if datetime_str:
            try:
                metadata['datetime_original'] = datetime.strptime(
                    datetime_str, '%Y:%m:%d %H:%M:%S'
                )
            except:
                pass
        
        gps_info = exif_data.get('GPSInfo')
        if gps_info and isinstance(gps_info, dict):
            gps_data = {}
            for tag_id, value in gps_info.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                gps_data[tag] = value
            
            lat, lon = ImageService._parse_gps_coordinates(gps_data)
            metadata['gps_latitude'] = lat
            metadata['gps_longitude'] = lon
        
        # Lưu các trường bổ sung
        extra_fields = [
            'Software', 'Artist', 'Copyright', 'ImageDescription',
            'ExposureTime', 'FNumber', 'ISO', 'FocalLength', 'Flash'
        ]
        for field in extra_fields:
            if field in exif_data:
                metadata['extra'][field] = str(exif_data[field])
        
        return metadata

    @staticmethod
    def _parse_gps_coordinates(
        gps_data: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Phân tích tọa độ GPS từ dữ liệu GPS EXIF."""
        try:
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef')
            lon = gps_data.get('GPSLongitude')
            lon_ref = gps_data.get('GPSLongitudeRef')
            
            if not all([lat, lat_ref, lon, lon_ref]):
                return None, None
            
            latitude = ImageService._convert_to_degrees(lat)
            if lat_ref == 'S':
                latitude = -latitude
                
            longitude = ImageService._convert_to_degrees(lon)
            if lon_ref == 'W':
                longitude = -longitude
                
            return latitude, longitude
        except:
            return None, None

    @staticmethod
    def _convert_to_degrees(value) -> float:
        """Chuyển đổi tọa độ GPS sang độ thập phân."""
        try:
            d, m, s = value
            return float(d) + float(m) / 60.0 + float(s) / 3600.0
        except:
            return 0.0

    @staticmethod
    def preprocess_for_ocr(image_data: bytes) -> bytes:
        """
        Tiền xử lý hình ảnh để có kết quả OCR tốt hơn.
        
        Args:
            image_data: Dữ liệu hình ảnh nhị phân
            
        Returns:
            Dữ liệu hình ảnh đã tiền xử lý
        """
        try:
            image = Image.open(BytesIO(image_data))
            
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            
            output = BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            print(f"Lỗi khi tiền xử lý hình ảnh: {str(e)}")
            return image_data


# Instance singleton
image_service = ImageService()
