# All imports
import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

# Configuration
Base = declarative_base()

# All classes representing database structure
# Class for data on all users
class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False) #name of user
    email = Column(String(250), nullable=False) #email id of user
    picture = Column(String(250)) #image of user, if available
    # provider = Column(String(25))

# Class for data on all categories
class Categories(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False) #name of category
    user_id = Column(Integer, ForeignKey('users.id')) #item added by which user
    user = relationship(Users)

    # Return item data in serializable format (for JSON endpoints)
    @property
    def serialize(self):
        return {
            'id': self.id,
            'category_name': self.name            
        }

# Class for data on all items
class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False) #name of item
    description = Column(String(), nullable=False) #description of the item    
    user_id = Column(Integer, ForeignKey('users.id')) #item added by which user
    category_id = Column(Integer, ForeignKey('categories.id')) #item belongs to which category
    category = relationship("Categories", backref=backref("items", cascade="all, delete"))
    user = relationship(Users)

    # Return item data in serializable format (for JSON endpoints)
    @property
    def serialize(self):
        return {
            'id': self.id,
            'item_name': self.name,
            'description': self.description,
        }

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)        