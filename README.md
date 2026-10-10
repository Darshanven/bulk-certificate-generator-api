# Bulk Certificate Generator API

A FastAPI backend that accepts one bulk request, validates recipient records, generates PDF certificates from a fixed template, tracks job progress, and exposes downloads.

## Features
- Bulk request accepts 1 to 500 recipients.
- SQLite persistence for jobs and recipient-level status.
- PDF certificates generated with ReportLab.
- Individual failures do not stop the rest of the batch.
- Job status, progress, and result endpoints.
- Download endpoint for each successful certificate.
- Tests for job creation, validation, generation, progress, failure isolation, and downloads.
- Interactive API documentation at `/docs`.

## Setup
Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install and run:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## API

### `GET /health`
Returns `{"status":"ok"}`.

### `POST /api/jobs/`
Example body:
```json
{
  "recipients": [
    {"name": "Asha Rao", "email": "asha@example.com", "course": "Python Basics"},
    {"name": "Ravi Kumar", "email": "ravi@example.com", "course": "Data Analytics"}
  ]
}
```
Returns HTTP 202 with a job ID and recipient IDs. The job is processed in a FastAPI background task.

### `GET /api/jobs/{job_id}/`
Returns job status, counts, percentage progress, and recipient-level status.

### `GET /api/jobs/{job_id}/results/`
Returns a concise result summary and errors for failed recipients.

### `GET /api/jobs/{job_id}/certificates/{recipient_id}/`
Downloads the successful recipient's PDF. Returns 404 for an unknown recipient or missing file, and 409 if generation has not succeeded.

## Tests
Run:
```bash
pytest -q
```

## Architecture
1. Pydantic validates recipient fields and request size.
2. The API stores a job and recipient records in SQLite through SQLAlchemy.
3. A background task processes each recipient separately.
4. ReportLab creates one PDF per recipient using a fixed template.
5. The worker records each result and updates job counters.
6. Clients poll job status and download successful certificates.

## Design decisions
- FastAPI provides typed validation and OpenAPI documentation.
- SQLite keeps local setup simple. PostgreSQL is a production alternative.
- One fixed PDF template meets the assignment scope without building a template editor.
- Each recipient has an isolated exception handler, so one failed PDF does not stop the batch.
- FastAPI `BackgroundTasks` keeps this assignment easy to run, but it is not durable if the process stops. A production version should use Celery/RQ with Redis.
- PDFs are stored on local disk. Production deployments should use object storage and authenticated download links.
- The request is limited to 500 recipients to control resource use.

## Learning
This project demonstrates REST API design, Pydantic validation, relational data modeling, background processing, PDF generation, error isolation, and automated testing.

## Future scope
- Durable task queue, retries, and worker monitoring.
- PostgreSQL for concurrent production workloads.
- Object storage and ZIP downloads.
- Authentication, rate limiting, and audit logs.
- Certificate IDs, issue dates, and public verification URLs.
- Structured logging and metrics.

## Limitations
This is an assignment implementation, not a hardened production service. Review the code, run the tests, and be ready to explain the trade-offs during the interview.
