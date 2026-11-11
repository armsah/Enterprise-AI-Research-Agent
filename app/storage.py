import logging
from uuid import UUID

from sqlalchemy import Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings
from app.models import ResearchReport

logger = logging.getLogger(__name__)
Base = declarative_base()


class ResearchRecord(Base):
    __tablename__ = "research_reports"

    research_id = Column(String(36), primary_key=True)
    question = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)


class ResearchStorage:
    """Persist and retrieve structured research reports."""

    def __init__(self, database_url: str | None = None):
        url = database_url or get_settings().database_url
        self.engine = create_engine(
            url, pool_pre_ping=True,
            connect_args={"check_same_thread": False}
            if url.startswith("sqlite:") else {},
        )
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)

    def initialize(self):
        Base.metadata.create_all(self.engine)

    def save(self, report: ResearchReport) -> None:
        record = ResearchRecord(
            research_id=str(report.research_id),
            question=report.question,
            status=report.status.value,
            report_json=report.model_dump_json(),
            created_at=report.created_at,
        )

        with self.sessions.begin() as session:
            session.merge(record)

    def get(self, research_id: UUID) -> ResearchReport | None:
        with self.sessions() as session:
            record = session.get(ResearchRecord, str(research_id))

            if record is None:
                return None

            return ResearchReport.model_validate_json(record.report_json)

    def close(self) -> None:
        self.engine.dispose()
