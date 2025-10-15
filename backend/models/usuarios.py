import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
# No necesitamos func para este paso:
# from sqlalchemy.sql import func 

# Define la base declarativa para los modelos ORM
Base = declarative_base()

class UserORM(Base):
    """
    Modelo ORM de SQLAlchemy para la tabla 'users'.
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    nombre = Column(String, nullable=True)
    
    # CLAVE: Dejamos el campo sin default para que el router lo maneje.
    fecha_creacion = Column(DateTime) 

    def __repr__(self):
        return f"<UserORM(id={self.user_id}, email='{self.email}')>"
        