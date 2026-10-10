from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base

class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id = Column(String, primary_key=True)
    status = Column(String, nullable=False, default="PENDING")
    total = Column(Integer, nullable=False, default=0)
    succeeded = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    recipients = relationship("CertificateRecipient", back_populates="job", cascade="all, delete-orphan")

class CertificateRecipient(Base):
    __tablename__ = "certificate_recipients"
    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("generation_jobs.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    course = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    certificate_path = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    job = relationship("GenerationJob", back_populates="recipients")
