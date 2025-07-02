from sqlalchemy.orm import Session
from models import ChatHistory
from typing import List, Optional
from datetime import datetime, timedelta, timezone

class DatabaseService:
    
    @staticmethod
    def save_chat(db: Session, user_feeling: str, ai_response: str, user_ip: str = None, session_id: str = None) -> ChatHistory:
        """Save a discussion/conversation to the database (user_feeling field stores the topic)"""
        chat_entry = ChatHistory(
            user_feeling=user_feeling,
            ai_response=ai_response,
            user_ip=user_ip,
            session_id=session_id
        )
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)
        return chat_entry
    
    @staticmethod
    def get_chat_history(db: Session, limit: int = 50, offset: int = 0) -> List[ChatHistory]:
        """Get chat history with pagination"""
        return db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_chat_by_id(db: Session, chat_id: int) -> Optional[ChatHistory]:
        """Get a specific chat by ID"""
        return db.query(ChatHistory).filter(ChatHistory.id == chat_id).first()
    
    @staticmethod
    def get_recent_chats(db: Session, hours: int = 24) -> List[ChatHistory]:
        """Get chats from the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return db.query(ChatHistory).filter(ChatHistory.created_at >= cutoff_time).order_by(ChatHistory.created_at.desc()).all()
    
    @staticmethod
    def get_chats_by_feeling(db: Session, feeling_keyword: str) -> List[ChatHistory]:
        """Get conversations that contain a specific topic keyword"""
        return db.query(ChatHistory).filter(ChatHistory.user_feeling.ilike(f"%{feeling_keyword}%")).order_by(ChatHistory.created_at.desc()).all()
    
    @staticmethod
    def get_chat_stats(db: Session) -> dict:
        """Get basic statistics about chat history"""
        total_chats = db.query(ChatHistory).count()
        recent_chats = db.query(ChatHistory).filter(
            ChatHistory.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
        ).count()
        
        return {
            "total_chats": total_chats,
            "chats_last_week": recent_chats
        }
    
    @staticmethod
    def delete_all_chats(db: Session) -> int:
        """Delete all conversation history and return the number of deleted records"""
        deleted_count = db.query(ChatHistory).count()
        db.query(ChatHistory).delete()
        db.commit()
        return deleted_count