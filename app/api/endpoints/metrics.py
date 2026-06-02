"""
Endpoints for querying and exporting usage metrics.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_

from app.api.deps import get_current_user
from app.models.user import User
from app.utils.metrics_logger import _get_engine, _metric_events_table

logger = logging.getLogger(__name__)

router = APIRouter()

EXPORT_COLUMNS = [
    "id", "timestamp", "module", "action", "user_id", "center",
    "workspace_id", "disease_type", "cohort_id", "cohort_size",
    "algorithm_type", "coe_response_time_ms", "message",
]


def _build_filters(
    module: Optional[str],
    action: Optional[str],
    center: Optional[str],
    from_date: Optional[datetime],
    to_date: Optional[datetime],
):
    conditions = []
    t = _metric_events_table
    if module:
        conditions.append(t.c.module == module)
    if action:
        conditions.append(t.c.action == action)
    if center:
        conditions.append(t.c.center == center)
    if from_date:
        conditions.append(t.c.timestamp >= from_date)
    if to_date:
        conditions.append(t.c.timestamp <= to_date)
    return conditions


@router.get("/logs", response_model=List[Dict[str, Any]])
def get_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    center: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(500, le=5000),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Query usage metric events. All filters are optional.
    Results are ordered by timestamp descending.
    """
    engine = _get_engine()
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics database not configured",
        )
    try:
        t = _metric_events_table
        conditions = _build_filters(module, action, center, from_date, to_date)
        stmt = select(t).order_by(t.c.timestamp.desc()).limit(limit)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        with engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [dict(row) for row in rows]
    except Exception as exc:
        logger.error("[METRICS] Error querying logs: %s", exc)
        raise HTTPException(status_code=500, detail="Error querying metrics")


@router.get("/export")
def export_logs(
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    center: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Export usage metric events as CSV. All filters are optional.
    Returns a downloadable CSV file.
    """
    engine = _get_engine()
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Metrics database not configured",
        )
    try:
        t = _metric_events_table
        conditions = _build_filters(module, action, center, from_date, to_date)
        stmt = select(*[t.c[col] for col in EXPORT_COLUMNS]).order_by(t.c.timestamp.asc())
        if conditions:
            stmt = stmt.where(and_(*conditions))
        with engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(EXPORT_COLUMNS)
        for row in rows:
            writer.writerow(list(row))

        output.seek(0)
        filename = f"raven_metrics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as exc:
        logger.error("[METRICS] Error exporting logs: %s", exc)
        raise HTTPException(status_code=500, detail="Error exporting metrics")
