from fastapi import FastAPI, Query, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
import google.generativeai as genai
from sqlalchemy.orm import Session
from models import get_db, create_tables, ChatHistory
from database_service import DatabaseService
from typing import List

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

app = FastAPI(title="PhD Companion API", description="An intellectual companion for brainstorming, planning, and developing ideas")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the main page
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/discuss")
async def discuss_topic(
    request: Request,
    topic: str = Query(..., description="What topic would you like to explore or discuss?"),
    db: Session = Depends(get_db)
):
    try:
        # Generate AI response
        prompt = f"""You are a PhD-level intellectual companion. The user wants to discuss: "{topic}"

Please provide a thoughtful, analytical response that:
- Demonstrates deep understanding of the subject
- Offers multiple perspectives or approaches
- Suggests concrete next steps or methodologies
- References relevant theories, frameworks, or best practices when appropriate
- Encourages critical thinking and further exploration

Respond as a knowledgeable colleague would in an academic or professional setting."""
        
        response = model.generate_content(prompt)
        ai_message = response.text if hasattr(response, "text") else "I'd be happy to explore this topic with you. Could you provide a bit more context about what specific aspect you'd like to focus on?"
        
        # Get user IP for basic tracking
        user_ip = request.client.host if request.client else None
        
        # Save to database
        chat_entry = DatabaseService.save_chat(
            db=db,
            user_feeling=topic,  # Reusing the field for topic
            ai_response=ai_message,
            user_ip=user_ip
        )
        
        return {
            "topic": topic,
            "response": ai_message,
            "chat_id": chat_entry.id,
            "timestamp": chat_entry.created_at.isoformat()
        }
    
    except Exception as e:
        # If database fails, still return the AI response
        prompt = f"""You are a PhD-level intellectual companion. The user wants to discuss: "{topic}"
        
Please provide a thoughtful, analytical response that demonstrates deep understanding and offers multiple perspectives."""
        response = model.generate_content(prompt)
        ai_message = response.text if hasattr(response, "text") else "I'd be happy to explore this topic with you. Could you provide a bit more context?"
        
        return {
            "topic": topic,
            "response": ai_message,
            "chat_id": None,
            "timestamp": None,
            "note": "Response generated but not saved to database"
        }

# Pydantic models for API responses
class ChatHistoryResponse(BaseModel):
    id: int
    user_feeling: str
    ai_response: str
    created_at: str
    user_ip: str = None

    class Config:
        from_attributes = True

@app.get("/chat-history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    limit: int = Query(50, description="Number of conversations to retrieve", le=100),
    offset: int = Query(0, description="Number of conversations to skip"),
    db: Session = Depends(get_db)
):
    """Get conversation history with pagination"""
    try:
        chats = DatabaseService.get_chat_history(db, limit=limit, offset=offset)
        return [
            ChatHistoryResponse(
                id=chat.id,
                user_feeling=chat.user_feeling,
                ai_response=chat.ai_response,
                created_at=chat.created_at.isoformat(),
                user_ip=chat.user_ip
            )
            for chat in chats
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/chat-history/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_by_id(chat_id: int, db: Session = Depends(get_db)):
    """Get a specific conversation by ID"""
    chat = DatabaseService.get_chat_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return ChatHistoryResponse(
        id=chat.id,
        user_feeling=chat.user_feeling,
        ai_response=chat.ai_response,
        created_at=chat.created_at.isoformat(),
        user_ip=chat.user_ip
    )

@app.get("/chat-stats")
async def get_chat_stats(db: Session = Depends(get_db)):
    """Get basic statistics about conversation history"""
    try:
        stats = DatabaseService.get_chat_stats(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/recent-chats", response_model=List[ChatHistoryResponse])
async def get_recent_chats(
    hours: int = Query(24, description="Number of hours to look back", le=168),  # Max 1 week
    db: Session = Depends(get_db)
):
    """Get conversations from the last N hours"""
    try:
        chats = DatabaseService.get_recent_chats(db, hours=hours)
        return [
            ChatHistoryResponse(
                id=chat.id,
                user_feeling=chat.user_feeling,
                ai_response=chat.ai_response,
                created_at=chat.created_at.isoformat(),
                user_ip=chat.user_ip
            )
            for chat in chats
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



@app.get("/search-chats", response_model=List[ChatHistoryResponse])
async def search_chats_by_feeling(
    feeling: str = Query(..., description="Search for conversations containing this topic keyword"),
    db: Session = Depends(get_db)
):
    """Search conversations by topic keyword"""
    try:
        chats = DatabaseService.get_chats_by_feeling(db, feeling)
        return [
            ChatHistoryResponse(
                id=chat.id,
                user_feeling=chat.user_feeling,
                ai_response=chat.ai_response,
                created_at=chat.created_at.isoformat(),
                user_ip=chat.user_ip
            )
            for chat in chats
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.delete("/chat-history")
async def delete_all_chat_history(db: Session = Depends(get_db)):
    """Delete all conversation history"""
    try:
        deleted_count = DatabaseService.delete_all_chats(db)
        return {
            "message": "Conversation history deleted successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
