import logging
from urllib.parse import urlparse

from pydantic import ValidationError

from app.config import get_settings
from app.graph import build_graph
from app.models import ResearchReport, ResearchRequest, ResearchStatus

logger = logging.getLogger(__name__)


class ResearchService:
    """Execute research workflows and return structured reports."""

    def __init__(self):
        self.graph = build_graph()

    def run(self, request: ResearchRequest, urls: list[str]) -> ResearchReport:
        settings = get_settings()

        if not isinstance(request, ResearchRequest):
            raise TypeError("A validated ResearchRequest is required.")

        if not urls:
            raise ValueError("At least one public source URL is required.")

        if len(urls) > settings.max_sources:
            raise ValueError("Too many source URLs.")

        for url in urls:
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("Only valid HTTP/HTTPS URLs are accepted.")

        try:
            result = self.graph.invoke(
                {
                    "request": request,
                    "urls": urls,
                    "sources": [],
                    "report": None,
                },
                config={"recursion_limit": settings.max_research_steps + 5},
            )

            report = result.get("report")

            if not isinstance(report, ResearchReport):
                raise RuntimeError("Research workflow returned no report.")

            return report

        except (ValidationError, ValueError, RuntimeError, Exception):
            logger.exception("Research workflow failed")

            return ResearchReport(
                question=request.question,
                status=ResearchStatus.FAILED,
                error="Research could not be completed.",
            )
