from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all of the ORM models"""

    # prevent base table from created
    __abstract__: bool = True