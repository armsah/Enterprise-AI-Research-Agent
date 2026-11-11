import os
import secrets
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.models import ResearchReport, ResearchRequest
from app.research import ResearchService
from app.storage import ResearchStorage
from app.telemetry import configure_logging, new_request_id, track_operation


class ResearchInput(ResearchRequest):
    urls: list[str] = Field(min_length=1, max_length=20)


def require_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv("RESEARCH_API_KEY")

    if not expected:
        raise HTTPException(503, "API authentication is not configured.")

    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Invalid API key.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    app.state.storage = ResearchStorage()
    app.state.storage.initialize()
    app.state.service = ResearchService()
    yield
    app.state.storage.close()


app = FastAPI(
    title="Enterprise AI Research Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/research",
    response_model=ResearchReport,
    dependencies=[Depends(require_api_key)],
)
def create_research(payload: ResearchInput):
    request_id = new_request_id()

    with track_operation("research", request_id):
        request = ResearchRequest(
            question=payload.question,
            max_sources=payload.max_sources,
            include_summary=payload.include_summary,
        )

        try:
            report = app.state.service.run(request, payload.urls)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

        app.state.storage.save(report)
        return report


@app.get(
    "/research/{research_id}",
    response_model=ResearchReport,
    dependencies=[Depends(require_api_key)],
)
def get_research(research_id: UUID):
    report = app.state.storage.get(research_id)

    if report is None:
        raise HTTPException(404, "Research report not found.")

    return report
