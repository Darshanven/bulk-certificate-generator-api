
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import GenerationJob, CertificateRecipient
from .certificate import generate_certificate

OUTPUT_DIR = Path(
    os.getenv("CERTIFICATE_OUTPUT_DIR", "./generated_certificates")
)


def process_job(job_id: str) -> None:
    db: Session = SessionLocal()

    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return

        job.status = "PROCESSING"
        db.commit()

        recipients = (
            db.query(CertificateRecipient)
            .filter_by(job_id=job_id)
            .all()
        )

        for recipient in recipients:
            try:
                output_path = OUTPUT_DIR / job_id / f"{recipient.id}.pdf"

                generate_certificate(
                    str(output_path),
                    recipient.name,
                    recipient.course,
                    recipient.email,
                )

                recipient.certificate_path = str(output_path)
                recipient.status = "SUCCEEDED"
                recipient.error = None

            except Exception as exc:
                recipient.status = "FAILED"
                recipient.error = (
                    f"Certificate generation failed: {type(exc).__name__}"
                )
                recipient.certificate_path = None

            db.commit()

        job = db.get(GenerationJob, job_id)
        if not job:
            return

        job.succeeded = sum(
            recipient.status == "SUCCEEDED" for recipient in recipients
        )
        job.failed = sum(
            recipient.status == "FAILED" for recipient in recipients
        )

        if job.failed == 0:
            job.status = "COMPLETED"
        elif job.succeeded == 0:
            job.status = "FAILED"
        else:
            job.status = "PARTIALLY_COMPLETED"

        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    finally:
        db.close()

