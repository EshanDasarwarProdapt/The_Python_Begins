from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    role = Column(String) # 'user' or 'ai'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
db_path = os.path.join(os.path.dirname(__file__), 'chat_history.db')
engine = create_engine(f'sqlite:///{db_path}', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def create_session(session_id: str, title: str = "New Chat"):
    db = SessionLocal()
    # Check if exists
    existing = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not existing:
        new_session = ChatSession(id=session_id, title=title)
        db.add(new_session)
        db.commit()
    db.close()

def get_all_sessions():
    db = SessionLocal()
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
    # convert to list of dicts to detach from session
    result = [{"id": s.id, "title": s.title} for s in sessions]
    db.close()
    return result

def get_messages(session_id: str):
    db = SessionLocal()
    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
    result = [{"role": m.role, "content": m.content} for m in messages]
    db.close()
    return result

def add_message(session_id: str, role: str, content: str):
    db = SessionLocal()
    new_msg = Message(session_id=session_id, role=role, content=content)
    db.add(new_msg)
    db.commit()
    db.close()

def update_session_title(session_id: str, title: str):
    db = SessionLocal()
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.title = title
        db.commit()
    db.close()
