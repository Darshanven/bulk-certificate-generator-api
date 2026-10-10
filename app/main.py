from pathlib import Path
from uuid import uuid4
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from .database import Base, engine, get_db
from .models import GenerationJob, CertificateRecipient
from .schemas import CreateJobRequest, JobResponse
from .worker import process_job

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bulk Certificate Generator API", version="1.0.0",
              description="Bulk PDF certificate generation with job tracking and downloads.")

def serialize_job(job: GenerationJob) -> dict:
    progress = 0.0 if not job.total else round((job.succeeded + job.failed) * 100 / job.total, 2)
    return {
        "id": job.id, "status": job.status, "total": job.total,
        "succeeded": job.succeeded, "failed": job.failed,
        "progress_percent": progress,
        "created_at": job.created_at.isoformat() if job.created_at else "",
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "recipients": [{"recipient_id": r.id, "name": r.name, "email": r.email,
                        "course": r.course, "status": r.status, "error": r.error}
                       for r in job.recipients]
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/jobs/", response_model=JobResponse, status_code=202)
def create_job(payload: CreateJobRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid4())
    job = GenerationJob(id=job_id, status="PENDING", total=len(payload.recipients))
    for item in payload.recipients:
        job.recipients.append(CertificateRecipient(
            id=str(uuid4()), name=item.name, email=item.email, course=item.course, status="PENDING"))
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job_id)
    return serialize_job(job)

@app.get("/api/jobs/{job_id}/", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).options(selectinload(GenerationJob.recipients)).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return serialize_job(job)

@app.get("/api/jobs/{job_id}/results/")
def get_results(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).options(selectinload(GenerationJob.recipients)).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return {"job_id": job.id, "status": job.status, "total": job.total,
            "succeeded": job.succeeded, "failed": job.failed,
            "recipients": serialize_job(job)["recipients"]}

@app.get("/api/jobs/{job_id}/certificates/{recipient_id}/")
def download_certificate(job_id: str, recipient_id: str, db: Session = Depends(get_db)):
    recipient = db.query(CertificateRecipient).filter_by(job_id=job_id, id=recipient_id).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient or certificate not found")
    if recipient.status != "SUCCEEDED" or not recipient.certificate_path:
        raise HTTPException(status_code=409, detail=f"Certificate is not available. Current status: {recipient.status}")
    path = Path(recipient.certificate_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Certificate file is missing")
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in recipient.name)
    return FileResponse(path, media_type="application/pdf", filename=f"certificate-{safe_name}.pdf")
