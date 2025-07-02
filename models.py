from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_feeling = Column(String(255), nullable=False)  # Stores topic/question (reusing field name for compatibility)
    ai_response = Column(Text, nullable=False)  # Stores PhD-level response
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user_ip = Column(String(45), nullable=True)  # To store user IP for basic tracking
    session_id = Column(String(255), nullable=True)  # For future session tracking

    def __repr__(self):
        return f"<ChatHistory(id={self.id}, topic='{self.user_feeling[:50]}...', created_at={self.created_at})>"

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()