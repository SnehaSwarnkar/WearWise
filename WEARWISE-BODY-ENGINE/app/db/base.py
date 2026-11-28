"""
WearWise Database Declarative Base
SQLAlchemy 2.0 declarative base for all persistence models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass
