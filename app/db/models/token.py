from app.core.database import Base
from sqlalchemy import Column, Integer, String 

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id = Column(Integer, primary_key=True)
    token = Column(String(500), unique=True, index=True)
