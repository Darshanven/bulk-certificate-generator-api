from pydantic import BaseModel, Field, field_validator
from typing import List

class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    course: str = Field(min_length=1, max_length=160)

    @field_validator("name", "email", "course")
    @classmethod
    def trim_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def basic_email_check(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value

class CreateJobRequest(BaseModel):
    recipients: List[RecipientInput] = Field(min_length=1, max_length=500)

class RecipientResult(BaseModel):
    recipient_id: str
    name: str
    email: str
    course: str
    status: str
    error: str | None = None

class JobResponse(BaseModel):
    id: str
    status: str
    total: int
    succeeded: int
    failed: int
    progress_percent: float
    created_at: str
    completed_at: str | None
    recipients: list[RecipientResult]
