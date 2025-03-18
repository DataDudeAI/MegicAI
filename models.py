from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    credits = Column(Float, default=10.0)

class Prompt(Base):
    __tablename__ = 'prompts'

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    description = Column(String, nullable=True)
    creator_id = Column(String, index=True)
