from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, Boolean
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
    frame_count = Column(Integer, nullable=False)
    frame_rate = Column(Float, nullable=False)
    frame_width = Column(Integer, nullable=False)
    frame_height = Column(Integer, nullable=False)
    video_format = Column(String, nullable=False)
    tos_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploading", comment="状态: uploading/ready/failed")
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开")
    visible_to_user_ids = Column(Text, nullable=True, comment="管理员指定的可见用户ID列表，JSON格式")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", backref="videos")
