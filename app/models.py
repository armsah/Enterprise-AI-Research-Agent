from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl


class ResearchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchRequest(BaseModel):
    question: str = Field(min_length=10, max_length=2000)
    max_sources: int = Field(default=5, ge=1, le=20)
    include_summary: bool = True


class ResearchSource(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    snippet: str = Field(max_length=3000)
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ResearchReport(BaseModel):
    research_id: UUID = Field(default_factory=uuid4)
    question: str
    status: ResearchStatus = ResearchStatus.PENDING
    summary: str = ""
    findings: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    model_used: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error: str | None = None
