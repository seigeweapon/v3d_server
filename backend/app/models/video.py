from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    studio = Column(String, nullable=False)
    producer = Column(String, nullable=False)
    production = Column(String, nullable=False)
    action = Column(String, nullable=False)
    camera_count = Column(Integer, nullable=False)
    prime_camera_number = Column(Integer, nullable=False)
    background_id = Column(Integer, ForeignKey("backgrounds.id"), nullable=False)
    calibration_id = Column(Integer, ForeignKey("calibrations.id"), nullable=False)
    frame_count = Column(Integer, nullable=False)
    frame_rate = Column(Float, nullable=False)
    frame_width = Column(Integer, nullable=False)
    frame_height = Column(Integer, nullable=False)
    video_format = Column(String, nullable=False)
    tos_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", backref="videos")
