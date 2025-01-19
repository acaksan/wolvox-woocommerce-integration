import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from src.config.settings import Settings

# Rich konsol ve traceback kurulumu
console = Console()
install_rich_traceback(show_locals=True)

class Logger:
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.settings = Settings()
        self.setup_logging()
    
    def setup_logging(self):
        """Loglama sistemini kur"""
        try:
            # Log dizinini oluştur
            log_dir = Path(self.settings.get('paths.logs'))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Temel log ayarları
            log_config = self.settings.get('logging')
            log_level = getattr(logging, log_config['level'].upper())
            log_format = log_config['format']
            
            # Kök logger'ı yapılandır
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[RichHandler(console=console, rich_tracebacks=True)]
            )
            
            # Varsayılan handler'ları temizle
            root_logger = logging.getLogger()
            if root_logger.handlers:
                root_logger.handlers.clear()
            
            # Dosya handler'ı
            log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=log_config['file_size'],
                backupCount=log_config['backup_count'],
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)
            
            # Konsol handler'ı
            if log_config['console_output']:
                console_handler = RichHandler(console=console, rich_tracebacks=True)
                console_handler.setFormatter(logging.Formatter('%(message)s'))
                root_logger.addHandler(console_handler)
            
            # JSON handler'ı (detaylı loglama için)
            json_log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.json"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=log_config['file_size'],
                backupCount=log_config['backup_count'],
                encoding='utf-8'
            )
            json_handler.setFormatter(JsonFormatter())
            root_logger.addHandler(json_handler)
            
        except Exception as e:
            print(f"Loglama sistemi kurulurken hata oluştu: {str(e)}")
            raise
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Belirtilen isimde logger döndür"""
        if name is None:
            return logging.getLogger()
            
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]

class JsonFormatter(logging.Formatter):
    """JSON formatında log kaydı oluşturan formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını JSON formatına dönüştür"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Hata detayları
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Ekstra alanlar
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra
        
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Logger oluştur ve yapılandır"""
    return Logger().get_logger(name)
