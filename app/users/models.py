from sqlalchemy import Column, Integer, String
from app.database import Base

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)