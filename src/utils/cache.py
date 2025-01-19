from typing import Any, Optional, Union, Callable
from datetime import datetime, timedelta
import json
import pickle
import hashlib
import logging
from functools import wraps
from pathlib import Path
import threading
import time

from src.config.settings import Settings
from src.utils.logger import setup_logger

class Cache:
    """Önbellek yöneticisi"""
    
    _instance = None
    _cache = {}
    _file_cache_dir = Path('data/cache')
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Cache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        
        # Cache ayarlarını al
        cache_config = self.settings.get('cache')
        self.enabled = cache_config['enabled']
        self.ttl = cache_config['ttl']
        self.max_size = cache_config['max_size']
        
        # Cache dizinini oluştur
        self._file_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Temizleme thread'ini başlat
        self._start_cleanup_thread()
    
    def _generate_key(self, key: Union[str, tuple]) -> str:
        """Cache anahtarı oluştur"""
        if isinstance(key, tuple):
            key = '_'.join(str(k) for k in key)
        return hashlib.md5(str(key).encode()).hexdigest()
    
    def _serialize(self, value: Any) -> bytes:
        """Değeri serialize et"""
        try:
            return pickle.dumps(value)
        except Exception as e:
            self.logger.error(f"Serileştirme hatası: {str(e)}")
            return pickle.dumps(None)
    
    def _deserialize(self, value: bytes) -> Any:
        """Değeri deserialize et"""
        try:
            return pickle.loads(value)
        except Exception as e:
            self.logger.error(f"Deserileştirme hatası: {str(e)}")
            return None
    
    def _is_expired(self, timestamp: float) -> bool:
        """Cache değerinin süresi dolmuş mu kontrol et"""
        return time.time() - timestamp > self.ttl
    
    def _cleanup_memory_cache(self):
        """Bellek önbelleğini temizle"""
        with self._lock:
            # Süresi dolmuş değerleri temizle
            expired_keys = [
                k for k, v in self._cache.items()
                if self._is_expired(v['timestamp'])
            ]
            for k in expired_keys:
                del self._cache[k]
            
            # Boyut sınırını aş
            if len(self._cache) > self.max_size:
                # En eski değerleri sil
                sorted_items = sorted(
                    self._cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                for k, _ in sorted_items[:len(self._cache) - self.max_size]:
                    del self._cache[k]
    
    def _cleanup_file_cache(self):
        """Dosya önbelleğini temizle"""
        try:
            for cache_file in self._file_cache_dir.glob('*.cache'):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                        if self._is_expired(data['timestamp']):
                            cache_file.unlink()
                except Exception:
                    # Bozuk cache dosyasını sil
                    cache_file.unlink()
        except Exception as e:
            self.logger.error(f"Dosya önbelleği temizlenirken hata: {str(e)}")
    
    def _start_cleanup_thread(self):
        """Temizleme thread'ini başlat"""
        def cleanup_task():
            while True:
                try:
                    self._cleanup_memory_cache()
                    self._cleanup_file_cache()
                except Exception as e:
                    self.logger.error(f"Önbellek temizleme hatası: {str(e)}")
                finally:
                    time.sleep(300)  # 5 dakika bekle
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()
    
    def get(self, key: Union[str, tuple], default: Any = None) -> Any:
        """Önbellekten değer al"""
        if not self.enabled:
            return default
            
        cache_key = self._generate_key(key)
        
        # Önce bellekten kontrol et
        with self._lock:
            if cache_key in self._cache:
                data = self._cache[cache_key]
                if not self._is_expired(data['timestamp']):
                    return data['value']
                del self._cache[cache_key]
        
        # Dosyadan kontrol et
        cache_file = self._file_cache_dir / f"{cache_key}.cache"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    if not self._is_expired(data['timestamp']):
                        # Belleğe al
                        with self._lock:
                            self._cache[cache_key] = data
                        return data['value']
                cache_file.unlink()
            except Exception as e:
                self.logger.error(f"Cache dosyası okuma hatası: {str(e)}")
                try:
                    cache_file.unlink()
                except Exception:
                    pass
        
        return default
    
    def set(self, key: Union[str, tuple], value: Any, ttl: Optional[int] = None) -> bool:
        """Önbelleğe değer kaydet"""
        if not self.enabled:
            return False
            
        cache_key = self._generate_key(key)
        timestamp = time.time()
        
        data = {
            'value': value,
            'timestamp': timestamp,
            'ttl': ttl or self.ttl
        }
        
        try:
            # Belleğe kaydet
            with self._lock:
                self._cache[cache_key] = data
            
            # Dosyaya kaydet
            cache_file = self._file_cache_dir / f"{cache_key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Cache kaydetme hatası: {str(e)}")
            return False
    
    def delete(self, key: Union[str, tuple]) -> bool:
        """Önbellekten değer sil"""
        if not self.enabled:
            return False
            
        cache_key = self._generate_key(key)
        
        try:
            # Bellekten sil
            with self._lock:
                if cache_key in self._cache:
                    del self._cache[cache_key]
            
            # Dosyadan sil
            cache_file = self._file_cache_dir / f"{cache_key}.cache"
            if cache_file.exists():
                cache_file.unlink()
            
            return True
        except Exception as e:
            self.logger.error(f"Cache silme hatası: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Tüm önbelleği temizle"""
        if not self.enabled:
            return False
            
        try:
            # Belleği temizle
            with self._lock:
                self._cache.clear()
            
            # Dosyaları temizle
            for cache_file in self._file_cache_dir.glob('*.cache'):
                cache_file.unlink()
            
            return True
        except Exception as e:
            self.logger.error(f"Cache temizleme hatası: {str(e)}")
            return False

def cached(ttl: Optional[int] = None):
    """Cache decorator'ı"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not Cache().enabled:
                return func(*args, **kwargs)
            
            # Cache anahtarı oluştur
            key = (
                func.__name__,
                str(args),
                str(sorted(kwargs.items()))
            )
            
            # Önbellekten kontrol et
            result = Cache().get(key)
            if result is not None:
                return result
            
            # Fonksiyonu çalıştır ve sonucu önbelleğe al
            result = func(*args, **kwargs)
            Cache().set(key, result, ttl)
            
            return result
        return wrapper
    return decorator
