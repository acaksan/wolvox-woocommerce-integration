import requests
from requests.adapters import HTTPAdapter, Retry
from typing import Any, Dict, Optional, Union
import json
import time
from datetime import datetime
import hashlib
import hmac
import base64
from urllib.parse import urlencode
import logging

from src.config.settings import Settings
from src.utils.logger import setup_logger

class APIClient:
    """Temel API istemci sınıfı"""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = setup_logger(self.__class__.__name__)
        
        # API ayarlarını al
        api_config = self.settings.get('api')
        self.timeout = api_config['timeout']
        self.max_retries = api_config['max_retries']
        self.retry_delay = api_config['retry_delay']
        
        # Session oluştur
        self.session = self._create_session()
        
        # Rate limiting
        self.rate_limit = api_config['rate_limit']
        self.rate_limit_period = api_config['rate_limit_period']
        self.request_times = []
    
    def _create_session(self) -> requests.Session:
        """Yeni bir HTTP session oluştur"""
        session = requests.Session()
        
        # Retry stratejisi
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        # HTTP adapter'ı yapılandır
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _check_rate_limit(self):
        """Rate limit kontrolü yap"""
        current_time = time.time()
        
        # Eski istekleri temizle
        self.request_times = [t for t in self.request_times 
                            if current_time - t < self.rate_limit_period]
        
        # Rate limit kontrolü
        if len(self.request_times) >= self.rate_limit:
            sleep_time = self.request_times[0] + self.rate_limit_period - current_time
            if sleep_time > 0:
                self.logger.warning(f"Rate limit aşıldı. {sleep_time:.2f} saniye bekleniyor...")
                time.sleep(sleep_time)
        
        self.request_times.append(current_time)
    
    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """HTTP başlıklarını hazırla"""
        default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': f"{self.settings.get('app.name')}/{self.settings.get('app.version')}"
        }
        
        if headers:
            default_headers.update(headers)
        
        return default_headers
    
    def _sign_request(self, method: str, url: str, data: Optional[Dict] = None,
                     secret_key: Optional[str] = None) -> str:
        """İsteği imzala"""
        if not secret_key:
            return ""
            
        # İmza için string oluştur
        timestamp = str(int(time.time()))
        string_to_sign = f"{method.upper()}\n{url}\n{timestamp}\n"
        
        if data:
            if isinstance(data, dict):
                sorted_data = json.dumps(data, sort_keys=True)
            else:
                sorted_data = str(data)
            string_to_sign += sorted_data
        
        # HMAC-SHA256 ile imzala
        signature = hmac.new(
            secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """API yanıtını işle"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            self.logger.error("JSON decode hatası")
            return {'error': 'Invalid JSON response'}
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP hatası: {str(e)}")
            return {'error': str(e)}
        except Exception as e:
            self.logger.error(f"Beklenmeyen hata: {str(e)}")
            return {'error': str(e)}
    
    def request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """HTTP isteği gönder"""
        self._check_rate_limit()
        
        # Headers hazırla
        headers = self._prepare_headers(kwargs.pop('headers', None))
        
        # İmza ekle
        if 'sign_key' in kwargs:
            sign_key = kwargs.pop('sign_key')
            signature = self._sign_request(method, url, kwargs.get('json'), sign_key)
            headers['X-Signature'] = signature
        
        try:
            start_time = time.time()
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                **kwargs
            )
            end_time = time.time()
            
            # İstek logla
            self.logger.info(
                f"API İsteği: {method} {url} "
                f"(Süre: {(end_time - start_time):.2f}s, "
                f"Durum: {response.status_code})"
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            self.logger.error(f"İstek zaman aşımına uğradı: {url}")
            return {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Bağlantı hatası: {url}")
            return {'error': 'Connection error'}
        except Exception as e:
            self.logger.error(f"İstek hatası: {str(e)}")
            return {'error': str(e)}
    
    def get(self, url: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """GET isteği gönder"""
        return self.request('GET', url, params=params, **kwargs)
    
    def post(self, url: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """POST isteği gönder"""
        return self.request('POST', url, json=data, **kwargs)
    
    def put(self, url: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PUT isteği gönder"""
        return self.request('PUT', url, json=data, **kwargs)
    
    def patch(self, url: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """PATCH isteği gönder"""
        return self.request('PATCH', url, json=data, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        """DELETE isteği gönder"""
        return self.request('DELETE', url, **kwargs)
