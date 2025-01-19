import os
from pathlib import Path
from typing import Any, Dict, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Settings:
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Ayarları yükle"""
        self.settings_file = os.path.join("data", "settings.json")
        self.logger = logging.getLogger(__name__)
        self._initialized = False
        self.load_settings()
    
    def load_settings(self):
        """Yapılandırma dosyasını yükle"""
        try:
            config_path = Path('src/config/settings.json')
            
            # Varsayılan ayarlar
            default_settings = {
                "app": {
                    "name": "Wolvox - WooCommerce Entegrasyon",
                    "version": "1.0.0",
                    "debug": False,
                    "log_level": "INFO",
                    "language": "tr",
                    "theme": "light",
                    "auto_sync": True,
                    "sync_interval": 300,  # 5 dakika
                },
                "paths": {
                    "logs": "logs",
                    "data": "data",
                    "backup": "backup",
                    "temp": "temp"
                },
                "database": {
                    "type": "sqlite",
                    "name": "sync.db",
                    "pool_size": 10,
                    "max_overflow": 20,
                    "pool_timeout": 30,
                    "pool_recycle": 1800
                },
                "sync": {
                    "batch_size": 100,
                    "retry_count": 3,
                    "retry_delay": 5,
                    "conflict_resolution": "newer",
                    "auto_categorize": True,
                    "image_sync": True,
                    "stock_sync": True,
                    "price_sync": True
                },
                "security": {
                    "jwt_secret": os.urandom(32).hex(),
                    "jwt_algorithm": "HS256",
                    "jwt_expires": 3600,
                    "password_min_length": 8,
                    "failed_login_limit": 5,
                    "lockout_duration": 300,
                    "session_timeout": 3600,
                    "require_2fa": False
                },
                "ui": {
                    "items_per_page": 50,
                    "date_format": "DD.MM.YYYY",
                    "time_format": "HH:mm:ss",
                    "currency_format": "₺#,##0.00",
                    "animations": True,
                    "notifications": True,
                    "auto_refresh": True,
                    "refresh_interval": 60
                },
                "api": {
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1,
                    "batch_size": 100,
                    "rate_limit": 50,
                    "rate_limit_period": 60
                },
                "cache": {
                    "enabled": True,
                    "type": "memory",
                    "ttl": 300,
                    "max_size": 1000
                },
                "notifications": {
                    "email": {
                        "enabled": False,
                        "smtp_host": "",
                        "smtp_port": 587,
                        "smtp_user": "",
                        "smtp_password": "",
                        "from_address": "",
                        "use_tls": True
                    },
                    "desktop": {
                        "enabled": True,
                        "sound": True,
                        "position": "bottom-right"
                    }
                },
                "backup": {
                    "enabled": True,
                    "interval": 86400,  # 24 saat
                    "keep_days": 7,
                    "compress": True,
                    "include_images": True
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_size": 10485760,  # 10MB
                    "backup_count": 5,
                    "console_output": True
                },
                "wolvox": {
                    "host": "localhost",
                    "database": "E:/AKINSOFT/Wolvox8/Database_FB/100/2024/WOLVOX.FDB",
                    "username": "SYSDBA",
                    "password": "masterkey",
                    "charset": "UTF8"
                },
                "woo": {
                    "url": "https://lastik-al.com",
                    "key": "ck_14ca8aab6f546bb34e5fd7f27ab0f77c6728c066",
                    "secret": "cs_62e4007a181e06ed919fa469baaf6e3fac8ea45f",
                    "version": "wc/v3"
                }
            }
            
            # Ayarlar dosyası varsa yükle
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    # Varsayılan ayarları kullanıcı ayarlarıyla birleştir
                    self._merge_settings(default_settings, user_settings)
            else:
                # Varsayılan ayarları kaydet
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4, ensure_ascii=False)
                self._config = default_settings
            
            # Dizinleri oluştur
            for path in self._config['paths'].values():
                Path(path).mkdir(parents=True, exist_ok=True)
            
            self.logger.info("Ayarlar başarıyla yüklendi")
            
        except Exception as e:
            self.logger.error(f"Ayarlar yüklenirken hata oluştu: {str(e)}")
            self._config = default_settings
    
    def _merge_settings(self, default: Dict, user: Dict, path: str = ""):
        """Varsayılan ayarları kullanıcı ayarlarıyla recursive olarak birleştir"""
        for key, value in default.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in user:
                user[key] = value
            elif isinstance(value, dict) and isinstance(user[key], dict):
                self._merge_settings(value, user[key], current_path)
        
        self._config = user
    
    def get(self, key: str, default: Any = None) -> Any:
        """Ayar değerini döndür"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                value = value[k]
            
            return value if value is not None else default
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Ayar değerini güncelle"""
        try:
            keys = key.split('.')
            config = self._config
            
            # Son anahtara kadar ilerle
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Son anahtarı güncelle
            config[keys[-1]] = value
            
            # Ayarları kaydet
            config_path = Path('src/config/settings.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Ayar güncellendi: {key} = {value}")
            
        except Exception as e:
            self.logger.error(f"Ayar güncellenirken hata oluştu: {str(e)}")
            raise
    
    def save(self):
        """Ayarları kaydet"""
        try:
            # Ayarları JSON formatında kaydet
            settings_data = {
                "woo": {
                    "url": self.get("woo.url"),
                    "key": self.get("woo.key"),
                    "secret": self.get("woo.secret"),
                    "version": self.get("woo.version")
                },
                "wolvox": {
                    "host": self.get("wolvox.host"),
                    "database": self.get("wolvox.database"),
                    "username": self.get("wolvox.username"),
                    "password": self.get("wolvox.password"),
                    "charset": self.get("wolvox.charset", "UTF8")
                },
                "sync": {
                    "interval": self.get("sync.interval", 5),
                    "auto_sync": self.get("sync.auto_sync", False),
                    "auto_match": self.get("sync.auto_match", True),
                    "sync_on_change": self.get("sync.sync_on_change", True),
                    "match_by_sku": self.get("sync.match_by_sku", True),
                    "match_by_name": self.get("sync.match_by_name", True),
                    "match_by_barcode": self.get("sync.match_by_barcode", False)
                },
                "app": {
                    "theme": self.get("app.theme", "Açık"),
                    "language": self.get("app.language", "Türkçe"),
                    "font_size": self.get("app.font_size", 12)
                }
            }
            
            # Ayarları kaydet
            config_path = Path('src/config/settings.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4, ensure_ascii=False)
            
            self.logger.info("Ayarlar başarıyla kaydedildi")
            
        except Exception as e:
            self.logger.error(f"Ayarlar kaydedilirken hata: {str(e)}")
            raise
    
    def reset(self):
        """Ayarları varsayılana sıfırla"""
        self._initialized = False
        self.__init__()
    
    @property
    def all(self) -> Dict[str, Any]:
        """Tüm ayarları döndür"""
        return self._config.copy()
