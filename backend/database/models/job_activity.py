from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.job import Job


class JobActivity(Base):
    """Append-only audit log for a job. Powers timeline + S3-014 analytics."""

    __tablename__ = "job_activity"

    activity_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.job_id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stage_change"
    )
    from_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="activities")

    __table_args__ = (Index("idx_job_activity_job", "job_id", "occurred_at"),)


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_job_activity(
    session: Session,
    job_id: int,
    *,
    event_type: str = "stage_change",
    from_stage: str | None = None,
    to_stage: str | None = None,
    notes: str | None = None,
) -> "JobActivity":
    activity = JobActivity(
        job_id=job_id,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        notes=notes,
        occurred_at=datetime.utcnow(),
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def get_job_activities(session: Session, job_id: int) -> list["JobActivity"]:
    rows = (
        session.execute(
            select(JobActivity)
            .where(JobActivity.job_id == job_id)
            .order_by(JobActivity.occurred_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def get_stage_analytics(session: Session, user_id: int) -> dict:
    """Conversion funnel and avg time-in-stage derived from job_activity events."""
    from database.models.job import Job

    rows: list[JobActivity] = (
        session.execute(
            select(JobActivity)
            .join(Job, JobActivity.job_id == Job.job_id)
            .where(Job.user_id == user_id)
            .order_by(JobActivity.occurred_at.asc())
        )
        .scalars()
        .all()
    )

    total_jobs = (
        session.execute(
            select(func.count()).select_from(Job).where(Job.user_id == user_id)
        ).scalar()
        or 0
    )

    # --- Conversion funnel ---
    funnel_pairs = [
        ("Applied", "Interview"),
        ("Interview", "Offer"),
        ("Offer", "Accepted"),
    ]

    # Collect distinct job_ids that ever entered each stage (via to_stage)
    entered: dict[str, set[int]] = {}
    # Collect distinct job_ids for each direct transition (from_stage → to_stage)
    transitioned: dict[tuple[str, str], set[int]] = {}

    for row in rows:
        if row.to_stage:
            entered.setdefault(row.to_stage, set()).add(row.job_id)
        if row.from_stage and row.to_stage:
            key = (row.from_stage, row.to_stage)
            transitioned.setdefault(key, set()).add(row.job_id)

    conversion_funnel: dict[str, float] = {}
    for from_s, to_s in funnel_pairs:
        denom = len(entered.get(from_s, set()))
        numer = len(transitioned.get((from_s, to_s), set()))
        rate = round(numer / denom * 100, 1) if denom else 0.0
        conversion_funnel[f"{from_s}→{to_s}"] = rate

    # Overall conversion: jobs ever in Offer or Accepted / total
    ever_converted = len(entered.get("Offer", set()) | entered.get("Accepted", set()))
    overall_conversion_rate = (
        round(ever_converted / total_jobs * 100, 1) if total_jobs else 0.0
    )

    # --- Avg time in stage ---
    # entry_times[job_id][stage] = occurred_at when job entered that stage
    # exit_times[job_id][stage] = occurred_at when job left that stage
    entry_times: dict[int, dict[str, datetime]] = {}
    exit_times: dict[int, dict[str, datetime]] = {}

    for row in rows:
        if row.to_stage:
            entry_times.setdefault(row.job_id, {})[row.to_stage] = row.occurred_at
        if row.from_stage:
            exit_times.setdefault(row.job_id, {})[row.from_stage] = row.occurred_at

    stage_durations: dict[str, list[float]] = {}
    for job_id, entries in entry_times.items():
        exits = exit_times.get(job_id, {})
        for stage, entered_at in entries.items():
            if stage in exits:
                delta_days = (exits[stage] - entered_at).total_seconds() / 86400
                if delta_days >= 0:
                    stage_durations.setdefault(stage, []).append(delta_days)

    avg_days_in_stage: dict[str, float] = {
        stage: round(sum(durations) / len(durations), 1)
        for stage, durations in stage_durations.items()
        if durations
    }

    return {
        "conversion_funnel": conversion_funnel,
        "overall_conversion_rate": overall_conversion_rate,
        "avg_days_in_stage": avg_days_in_stage,
    }
