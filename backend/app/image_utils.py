from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


def extract_exif_data(image_data: bytes) -> Dict[str, Any]:
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
        print(f"Error extracting EXIF: {str(e)}")
        return {}


def parse_image_metadata(exif_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    datetime_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
    if datetime_str:
        try:
            metadata['datetime_original'] = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
        except:
            pass
    
    gps_info = exif_data.get('GPSInfo')
    if gps_info:
        gps_data = {}
        for tag_id, value in gps_info.items():
            tag = GPSTAGS.get(tag_id, tag_id)
            gps_data[tag] = value
        
        lat, lon = _parse_gps_coordinates(gps_data)
        metadata['gps_latitude'] = lat
        metadata['gps_longitude'] = lon
    
    # Lưu các thông tin khác vào extra
    extra_fields = ['Software', 'Artist', 'Copyright', 'ImageDescription', 
                    'ExposureTime', 'FNumber', 'ISO', 'FocalLength', 'Flash']
    for field in extra_fields:
        if field in exif_data:
            metadata['extra'][field] = str(exif_data[field])
    
    return metadata


def _parse_gps_coordinates(gps_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    try:
        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef')
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef')
        
        if not all([lat, lat_ref, lon, lon_ref]):
            return None, None
        
        # Convert to decimal degrees
        latitude = _convert_to_degrees(lat)
        if lat_ref == 'S':
            latitude = -latitude
            
        longitude = _convert_to_degrees(lon)
        if lon_ref == 'W':
            longitude = -longitude
            
        return latitude, longitude
    except:
        return None, None


def _convert_to_degrees(value) -> float:
    try:
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    except:
        return 0.0
