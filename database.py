from sqlalchemy import Column, Integer, String, BLOB, DateTime, JSON, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timezone
import settings 
from zoneinfo import ZoneInfo

Base = declarative_base()

class DetectionHistory(Base):
    __tablename__ = "detection_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Jakarta")))
    original_image_name = Column(String, nullable=True) 
    original_image_blob = Column(BLOB, nullable=False) 
    detected_image_blob = Column(BLOB, nullable=False) 
    detections_data = Column(JSON) 

# Engine dan SessionLocal
engine = settings.engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Membuat tabel database jika belum ada."""
    Base.metadata.create_all(bind=engine)
