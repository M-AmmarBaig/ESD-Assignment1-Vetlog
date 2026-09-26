from datetime import datetime, timezone
import os
from app.config import DATABASE_URL
from app.metrics import raw_messages_total, raw_messages_last_captured_timestamp, raw_messages_db_size_bytes

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.event import api
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.sql.expression import false
from sqlalchemy import event
import time

from app.config import DATABASE_URL
from app.logger import logger

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
    },
    pool_size=5,
    max_overflow=10,
)

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.5:
        logger.warning(f"SLOW QUERY DETECTED ({total:.3f}s): {statement}")

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class RawMessage(Base):
    __tablename__ = "raw_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_name = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    display_name = Column(String, nullable=False)
    password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    thread_name = Column(String, nullable=False)
    turn_number = Column(Integer, nullable=False)
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tool_name = Column(String, nullable=True)
    tool_args = Column(Text, nullable=True)
    tool_output = Column(Text, nullable=True)
    report_path = Column(String(512), nullable=True)
    table_path = Column(String(512), nullable=True)
    tokens_used = Column(Integer, nullable=True)


class UserSetting(Base):
    __tablename__ = "user_settings"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(32), nullable=False, default="ollama")
    model = Column(String(128), nullable=False, default="")
    api_key = Column(Text, nullable=False, default="")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Metrics 

def _count_raw_messages() -> int:
    db = SessionLocal()
    try:
        return db.query(RawMessage).count()
    finally:
        db.close()

raw_messages_total.set_function(_count_raw_messages)

def _last_captured_timestamp() -> float:
    db = SessionLocal()
    try:
        latest = db.query(RawMessage.captured_at).order_by(RawMessage.captured_at.desc()).first()
        return latest[0].timestamp() if latest else 0
    finally:
        db.close()

raw_messages_last_captured_timestamp.set_function(_last_captured_timestamp)

def _db_file_size() -> int:
    path = DATABASE_URL.replace("sqlite:///", "")
    return os.path.getsize(path) if os.path.exists(path) else 0

raw_messages_db_size_bytes.set_function(_db_file_size)