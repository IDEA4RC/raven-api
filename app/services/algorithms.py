"""
Service for handling algorithms operations
"""

from abc import abstractmethod
from asyncio import tasks
from datetime import datetime, timezone
from typing import List, Optional
import logging
from urllib import response
import json

from app import db
from app.models.algorithm import Algorithm
from app.schemas.algorithms import (
    AlgorithmCreate,
    AlgorithmUpdate,
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.cohort_algorithm import CohortAlgorithm
from app.services.base import BaseService
from app.models.cohort import Cohort
from app.services.cohort import CohortService
from app.utils.constants import ALGORITHMS
import httpx

logger = logging.getLogger(__name__)

cohort_service = CohortService(Cohort)

from app.utils.constants import API_BASE, ALGORITHMS


class AlgorithmService(BaseService[Algorithm, AlgorithmCreate, AlgorithmUpdate]):

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url or API_BASE
        self.timeout = timeout

    def create_algorithm(self, db: Session, *, obj_in: AlgorithmCreate) -> Algorithm:
        """Create algorithm and link cohorts."""

        cohort_ids = obj_in.cohort_ids

        algorithm_data = obj_in.model_dump(exclude={"cohort_ids"})

        algorithm = Algorithm(**algorithm_data)

        if cohort_ids:
            cohorts = db.query(Cohort).filter(Cohort.id.in_(cohort_ids)).all()
            algorithm.cohorts = cohorts

        db.add(algorithm)
        db.commit()
        db.refresh(algorithm)

        return algorithm

    def get_algorithms_by_cohort(self, db: Session, cohort_id: int) -> List[Algorithm]:
        """Return algorithms linked to a cohort."""

        logger.info(
            "[ALGORITHMS] GET to get_algorithms_by_cohort with cohort_id: %s", cohort_id
        )
        return (
            db.query(Algorithm)
            .join(CohortAlgorithm, CohortAlgorithm.algorithm_id == Algorithm.id)
            .filter(CohortAlgorithm.cohort_id == cohort_id)
            .all()
        )

    def get_algorithms_by_exact_cohort_list(
        self, db: Session, cohort_ids: list[int]
    ) -> List[Algorithm]:

        logger.info(
            "[ALGORITHMS] GET to get_algorithms_by_exact_cohort_list with cohort_ids: %s",
            cohort_ids,
        )
        # Subquery: contar cohort_ids por algoritmo
        subq = (
            db.query(
                CohortAlgorithm.algorithm_id,
                func.count(CohortAlgorithm.cohort_id).label("total_cohorts"),
            )
            .group_by(CohortAlgorithm.algorithm_id)
            .subquery()
        )

        # Subquery: contar cuántos de los cohort_ids pasados están presentes
        match_count_subq = (
            db.query(
                CohortAlgorithm.algorithm_id,
                func.count(CohortAlgorithm.cohort_id).label("match_count"),
            )
            .filter(CohortAlgorithm.cohort_id.in_(cohort_ids))
            .group_by(CohortAlgorithm.algorithm_id)
            .subquery()
        )

        # Unimos las subqueries con Algorithm y filtramos por exact match
        query = (
            db.query(Algorithm)
            .join(subq, Algorithm.id == subq.c.algorithm_id)
            .join(match_count_subq, Algorithm.id == match_count_subq.c.algorithm_id)
            .filter(subq.c.total_cohorts == len(cohort_ids))
            .filter(match_count_subq.c.match_count == len(cohort_ids))
        )
        return query.all()

    def is_summary_cohort_list(
        self, db: Session, cohort_ids: list[int]
    ) -> List[Algorithm]:

        logger.info(
            "[ALGORITHMS] GET to is_summary_cohort_list with cohort_ids: %s",
            cohort_ids,
        )
        # Subquery: contar cohort_ids por algoritmo
        query = (
            db.query(Algorithm)
            .join(CohortAlgorithm)
            .filter(Algorithm.method_name == ALGORITHMS.SUMMARY)
            .group_by(Algorithm.id)
            .having(func.count(CohortAlgorithm.cohort_id) == len(cohort_ids))
            .having(
                func.count(
                    func.nullif(CohortAlgorithm.cohort_id.in_(cohort_ids), False)
                )
                == len(cohort_ids)
            )
        )
        return query.all()

    def get_all_algorithm(self, db: Session) -> List[Algorithm]:
        """Return algorithms linked to a cohort."""
        logger.info("[ALGORITHMS] GET to get_all_algorithm")
        return db.query(Algorithm).options(joinedload(Algorithm.cohorts)).all()

    def update_algorithm(self, db: Session, *, obj_in: AlgorithmUpdate) -> Algorithm:
        """Create algorithm and link cohorts."""

        task_id = obj_in.task_id
        logger.info(
            "[ALGORITHMS] UPDATE task: task_id=%s",
            task_id,
        )

        algorithm = db.query(Algorithm).filter(Algorithm.task_id == task_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with task_id {task_id} not found")

        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(algorithm, field, value)

        if not obj_in.version_date:
            algorithm.version_date = datetime.now(timezone.utc)

        db.add(algorithm)
        db.commit()
        db.refresh(algorithm)

        return algorithm

    def get_algorithm_statistics(self, *, access_token: str, task_id: int) -> int:
        """
        Obtiene el las estadísticas de un algoritmo de ejecución en Vantage6.
        """

        logger.info(
            "[V6] get_algorithm_statistics START for parent_task_id=%s", task_id
        )

        if not self.base_url:
            logger.warning("External data_preparation  URL not configured")
            return

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/task?id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()
            response_json = response.json()

            tasks = response_json.get("data", [])
            if not tasks:
                raise RuntimeError(f"No task found for id={task_id}")

            task_metadata = tasks[0]

            return task_metadata

        except (httpx.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.exception(
                "[V6] Error getting subtask for task_id=%s",
                task_id,
            )
            raise RuntimeError(f"Failed to retrieve subtask: {str(exc)}")


algorithm_service = AlgorithmService()
