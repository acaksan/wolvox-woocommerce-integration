from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import json
import re
import hashlib
import base64
import uuid
from pathlib import Path
import os
import shutil
from PIL import Image
import logging
from decimal import Decimal
import unicodedata
from slugify import slugify

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_unique_id() -> str:
    """Benzersiz ID oluştur"""
    return str(uuid.uuid4())

def hash_password(password: str) -> str:
    """Şifreyi hashle"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return base64.b64encode(salt + key).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Şifre doğrulama"""
    try:
        decoded = base64.b64decode(hashed.encode('utf-8'))
        salt = decoded[:32]
        key = decoded[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return key == new_key
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """Dosya adını temizle"""
    # Türkçe karakterleri değiştir
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ASCII', 'ignore').decode('ASCII')
    
    # Geçersiz karakterleri kaldır
    filename = re.sub(r'[^\w\s-]', '', filename)
    
    # Boşlukları tire ile değiştir
    filename = re.sub(r'[-\s]+', '-', filename).strip('-_')
    
    return filename.lower()

def create_slug(text: str) -> str:
    """SEO dostu slug oluştur"""
    return slugify(text, allow_unicode=True)

def format_price(price: Union[float, Decimal], currency: str = '₺') -> str:
    """Fiyat formatla"""
    try:
        if isinstance(price, str):
            price = Decimal(price)
        return f"{currency}{price:,.2f}"
    except Exception:
        return f"{currency}0.00"

def format_date(date_obj: Union[datetime, date], format_str: str = '%d.%m.%Y') -> str:
    """Tarih formatla"""
    try:
        return date_obj.strftime(format_str)
    except Exception:
        return ''

def parse_date(date_str: str, format_str: str = '%d.%m.%Y') -> Optional[datetime]:
    """Tarih ayrıştır"""
    try:
        return datetime.strptime(date_str, format_str)
    except Exception:
        return None

def format_file_size(size: int) -> str:
    """Dosya boyutunu formatla"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def ensure_dir(path: Union[str, Path]) -> Path:
    """Dizinin var olduğundan emin ol"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_delete(path: Union[str, Path]) -> bool:
    """Güvenli dosya/dizin silme"""
    try:
        path = Path(path)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        logger.error(f"Silme hatası: {str(e)}")
        return False

def optimize_image(image_path: Union[str, Path], max_size: int = 800,
                  quality: int = 85, format: str = 'JPEG') -> bool:
    """Görüntü optimize et"""
    try:
        image_path = Path(image_path)
        img = Image.open(image_path)
        
        # EXIF bilgisine göre döndür
        try:
            img = Image.open(image_path)
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif is not None:
                    orientation = exif.get(274)  # 274 = orientation
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
        except Exception as e:
            logger.warning(f"EXIF okuma hatası: {str(e)}")
        
        # Boyut değiştir
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.LANCZOS)
        
        # RGB'ye dönüştür
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Optimize edip kaydet
        img.save(
            image_path,
            format,
            quality=quality,
            optimize=True
        )
        
        return True
    except Exception as e:
        logger.error(f"Görüntü optimizasyon hatası: {str(e)}")
        return False

def validate_email(email: str) -> bool:
    """E-posta doğrula"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Telefon numarası doğrula"""
    pattern = r'^\+?[\d\s-]{10,}$'
    return bool(re.match(pattern, phone))

def mask_sensitive_data(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Hassas verileri maskele"""
    masked = data.copy()
    for field in fields:
        if field in masked:
            value = str(masked[field])
            if len(value) > 4:
                masked[field] = f"{value[:2]}{'*' * (len(value)-4)}{value[-2:]}"
            else:
                masked[field] = '*' * len(value)
    return masked

def diff_dicts(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """İki sözlük arasındaki farkları bul"""
    diff = {}
    for key in set(old) | set(new):
        if key not in old:
            diff[key] = {'old': None, 'new': new[key]}
        elif key not in new:
            diff[key] = {'old': old[key], 'new': None}
        elif old[key] != new[key]:
            diff[key] = {'old': old[key], 'new': new[key]}
    return diff

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """İki sözlüğü birleştir"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Sözlüğü düzleştir"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Düzleştirilmiş sözlüğü geri çevir"""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result

def to_bool(value: Any) -> bool:
    """Değeri boolean'a çevir"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 't', 'y', 'yes', 'on')
    if isinstance(value, (int, float)):
        return bool(value)
    return False

def to_int(value: Any, default: int = 0) -> int:
    """Değeri integer'a çevir"""
    try:
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except (ValueError, TypeError):
        return default

def to_float(value: Any, default: float = 0.0) -> float:
    """Değeri float'a çevir"""
    try:
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (ValueError, TypeError):
        return default

def to_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """Değeri Decimal'a çevir"""
    try:
        if isinstance(value, bool):
            return Decimal(int(value))
        return Decimal(str(value))
    except (ValueError, TypeError, decimal.InvalidOperation):
        return default

def truncate_string(text: str, length: int = 100, suffix: str = '...') -> str:
    """Metni belirli uzunlukta kes"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + suffix

def strip_html(text: str) -> str:
    """HTML etiketlerini temizle"""
    return re.sub(r'<[^>]+>', '', text)

def extract_urls(text: str) -> List[str]:
    """Metindeki URL'leri çıkar"""
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(pattern, text)

def is_valid_url(url: str) -> bool:
    """URL doğrula"""
    pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
    return bool(re.match(pattern, url))

def get_file_extension(filename: str) -> str:
    """Dosya uzantısını al"""
    return Path(filename).suffix.lower()[1:]

def is_image_file(filename: str) -> bool:
    """Dosyanın resim olup olmadığını kontrol et"""
    return get_file_extension(filename) in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp')
