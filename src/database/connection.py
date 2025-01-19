from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
from pathlib import Path

from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.engine = None
        self.Session = None
        self.session = None
        self.setup_database()
    
    def setup_database(self):
        """Veritabanı bağlantısını kur ve tabloları oluştur"""
        try:
            # SQLite veritabanı dosyası için dizin oluştur
            db_path = Path('data/sync.db')
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Veritabanı bağlantı URL'si
            database_url = f'sqlite:///{db_path}'
            
            # Engine oluştur
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False  # SQL loglarını göster/gizle
            )
            
            # Session factory oluştur
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            
            # Session oluştur
            self.session = self.Session()
            
            # Tabloları oluştur
            Base.metadata.create_all(self.engine)
            
            logger.info("Veritabanı bağlantısı başarıyla kuruldu")
            
        except Exception as e:
            logger.error(f"Veritabanı bağlantısı kurulamadı: {str(e)}")
            raise
    
    @contextmanager
    def session_scope(self):
        """Otomatik commit/rollback ile session context manager"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session(self):
        """Yeni bir veritabanı oturumu döndür"""
        return self.Session()
    
    def dispose(self):
        """Veritabanı bağlantısını kapat"""
        if self.engine:
            self.engine.dispose()
            logger.info("Veritabanı bağlantısı kapatıldı")
