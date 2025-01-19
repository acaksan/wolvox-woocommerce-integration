from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.database.connection import DatabaseManager
from src.utils.logger import setup_logger

# Generic tip için model tanımı
T = TypeVar('T')

class BaseService(Generic[T]):
    """Temel servis sınıfı"""
    
    def __init__(self, model: Type[T]):
        self.model = model
        self.db = DatabaseManager()
        self.logger = setup_logger(self.__class__.__name__)
    
    def create(self, data: Dict[str, Any]) -> Optional[T]:
        """Yeni kayıt oluştur"""
        try:
            with self.db.session_scope() as session:
                item = self.model(**data)
                session.add(item)
                session.flush()
                return item
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt oluşturulurken hata: {str(e)}")
            raise
    
    def get_by_id(self, id: int) -> Optional[T]:
        """ID'ye göre kayıt getir"""
        try:
            with self.db.session_scope() as session:
                return session.query(self.model).filter_by(id=id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt getirilirken hata: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Tüm kayıtları getir"""
        try:
            with self.db.session_scope() as session:
                return session.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıtlar getirilirken hata: {str(e)}")
            raise
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Kayıt güncelle"""
        try:
            with self.db.session_scope() as session:
                item = session.query(self.model).filter_by(id=id).first()
                if item:
                    for key, value in data.items():
                        setattr(item, key, value)
                    session.flush()
                return item
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt güncellenirken hata: {str(e)}")
            raise
    
    def delete(self, id: int) -> bool:
        """Kayıt sil"""
        try:
            with self.db.session_scope() as session:
                item = session.query(self.model).filter_by(id=id).first()
                if item:
                    session.delete(item)
                    return True
                return False
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt silinirken hata: {str(e)}")
            raise
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """Toplu kayıt oluştur"""
        try:
            with self.db.session_scope() as session:
                objects = [self.model(**item) for item in items]
                session.bulk_save_objects(objects)
                session.flush()
                return objects
        except SQLAlchemyError as e:
            self.logger.error(f"Toplu kayıt oluşturulurken hata: {str(e)}")
            raise
    
    def bulk_update(self, items: List[Dict[str, Any]]) -> List[T]:
        """Toplu kayıt güncelle"""
        try:
            with self.db.session_scope() as session:
                updated = []
                for item in items:
                    id = item.pop('id', None)
                    if id:
                        obj = session.query(self.model).filter_by(id=id).first()
                        if obj:
                            for key, value in item.items():
                                setattr(obj, key, value)
                            updated.append(obj)
                session.flush()
                return updated
        except SQLAlchemyError as e:
            self.logger.error(f"Toplu kayıt güncellenirken hata: {str(e)}")
            raise
    
    def bulk_delete(self, ids: List[int]) -> int:
        """Toplu kayıt sil"""
        try:
            with self.db.session_scope() as session:
                deleted = session.query(self.model).filter(
                    self.model.id.in_(ids)
                ).delete(synchronize_session=False)
                return deleted
        except SQLAlchemyError as e:
            self.logger.error(f"Toplu kayıt silinirken hata: {str(e)}")
            raise
    
    def count(self, **filters) -> int:
        """Kayıt sayısını getir"""
        try:
            with self.db.session_scope() as session:
                query = session.query(self.model)
                if filters:
                    query = query.filter_by(**filters)
                return query.count()
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt sayısı alınırken hata: {str(e)}")
            raise
    
    def exists(self, **filters) -> bool:
        """Kayıt var mı kontrol et"""
        try:
            with self.db.session_scope() as session:
                return session.query(
                    session.query(self.model).filter_by(**filters).exists()
                ).scalar()
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt kontrolü yapılırken hata: {str(e)}")
            raise
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[T, bool]:
        """Kayıt getir veya oluştur"""
        try:
            with self.db.session_scope() as session:
                instance = session.query(self.model).filter_by(**kwargs).first()
                if instance:
                    return instance, False
                else:
                    params = dict(kwargs)
                    if defaults:
                        params.update(defaults)
                    instance = self.model(**params)
                    session.add(instance)
                    session.flush()
                    return instance, True
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt getirme/oluşturma sırasında hata: {str(e)}")
            raise
    
    def update_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[T, bool]:
        """Kayıt güncelle veya oluştur"""
        try:
            with self.db.session_scope() as session:
                instance = session.query(self.model).filter_by(**kwargs).first()
                if instance:
                    for key, value in defaults.items() if defaults else {}:
                        setattr(instance, key, value)
                    created = False
                else:
                    params = dict(kwargs)
                    if defaults:
                        params.update(defaults)
                    instance = self.model(**params)
                    session.add(instance)
                    created = True
                session.flush()
                return instance, created
        except SQLAlchemyError as e:
            self.logger.error(f"Kayıt güncelleme/oluşturma sırasında hata: {str(e)}")
            raise
