from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# Ara tablolar
product_category_association = Table(
    'product_category_association',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

product_tag_association = Table(
    'product_tag_association',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    wolvox_id = Column(String(50), unique=True)
    woo_id = Column(Integer, unique=True)
    sku = Column(String(100), unique=True)
    name = Column(String(255))
    description = Column(String)
    short_description = Column(String)
    price = Column(Float)
    stock = Column(Integer)
    status = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ProductImage(Base):
    __tablename__ = 'product_images'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    woo_id = Column(Integer)
    src = Column(String)
    name = Column(String)
    alt = Column(String)
    position = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ProductVariation(Base):
    __tablename__ = 'product_variations'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    woo_id = Column(Integer)
    sku = Column(String(100))
    description = Column(String)
    regular_price = Column(Float)
    sale_price = Column(Float)
    stock_quantity = Column(Integer)
    stock_status = Column(String(20))
    attributes = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ProductAttribute(Base):
    __tablename__ = 'product_attributes'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    woo_id = Column(Integer)
    name = Column(String)
    position = Column(Integer)
    visible = Column(Boolean, default=True)
    variation = Column(Boolean, default=False)
    options = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    wolvox_id = Column(String(50))
    woo_id = Column(Integer)
    name = Column(String)
    slug = Column(String)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    description = Column(String)
    display = Column(String)
    image_id = Column(Integer)
    menu_order = Column(Integer)
    count = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    woo_id = Column(Integer)
    name = Column(String)
    slug = Column(String)
    description = Column(String)
    count = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SyncLog(Base):
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String)  # product, category, tag, etc.
    entity_id = Column(Integer)
    action = Column(String)  # create, update, delete
    status = Column(String)  # success, error
    message = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=func.now())

class Settings(Base):
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(JSON)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=func.now())
