"""
Metrics logger — writes usage events to an independent PostgreSQL database.
All calls are fire-and-forget: exceptions are caught internally and never
propagate to the caller.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings

logger = logging.getLogger(__name__)

_engine = None
_metric_events_table = None
_metadata = MetaData()

_metric_events_table = Table(
    "metric_events",
    _metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Column("module", String(50)),
    Column("action", String(50)),
    Column("user_id", String(100)),
    Column("center", String(50)),
    Column("workspace_id", Integer),
    Column("disease_type", String(20)),
    Column("cohort_id", Integer),
    Column("cohort_size", Integer),
    Column("algorithm_type", String(50)),
    Column("coe_response_time_ms", Integer),
    Column("message", Text),
    Column("extra", JSONB),
)


def _get_engine():
    global _engine
    if _engine is None:
        url = getattr(settings, "METRICS_DB_URL", None)
        if not url:
            return None
        _engine = create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=2)
    return _engine


def create_metrics_tables() -> None:
    """Create the metrics table if it does not exist. Called once at startup."""
    engine = _get_engine()
    if engine is None:
        logger.warning("[METRICS] METRICS_DB_URL not configured — metrics disabled")
        return
    try:
        _metadata.create_all(engine, checkfirst=True)
        logger.info("[METRICS] metrics_events table ready")
    except Exception as exc:
        logger.warning("[METRICS] Could not create metrics table: %s", exc)


def log_event(
    module: str,
    action: str,
    *,
    user_id: Optional[str] = None,
    center: Optional[str] = None,
    workspace_id: Optional[int] = None,
    disease_type: Optional[str] = None,
    cohort_id: Optional[int] = None,
    cohort_size: Optional[int] = None,
    algorithm_type: Optional[str] = None,
    coe_response_time_ms: Optional[int] = None,
    message: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """Insert a metric event. Never raises — safe to call from any service."""
    engine = _get_engine()
    if engine is None:
        return
    try:
        row = {
            "timestamp": datetime.now(timezone.utc),
            "module": module,
            "action": action,
            "user_id": user_id,
            "center": center,
            "workspace_id": workspace_id,
            "disease_type": disease_type,
            "cohort_id": cohort_id,
            "cohort_size": cohort_size,
            "algorithm_type": algorithm_type,
            "coe_response_time_ms": coe_response_time_ms,
            "message": message,
            "extra": extra,
        }
        with engine.begin() as conn:
            conn.execute(_metric_events_table.insert().values(**row))
    except SQLAlchemyError as exc:
        logger.warning("[METRICS] Failed to write event %s.%s: %s", module, action, exc)
    except Exception as exc:
        logger.warning("[METRICS] Unexpected error logging event %s.%s: %s", module, action, exc)
