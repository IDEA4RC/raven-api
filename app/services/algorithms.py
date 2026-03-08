"""
Service for handling algorithms operations
"""

from abc import abstractmethod
from datetime import datetime, timezone
from typing import List, Optional
import logging
from urllib import response

from app import db
from app.models.algorithm import Algorithm
from app.schemas.algorithms import AlgorithmCreate, AlgorithmUpdate
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.cohort_algorithm import CohortAlgorithm
from app.services.base import BaseService
from app.models.cohort import Cohort
from app.services.cohort import CohortService

logger = logging.getLogger(__name__)

cohort_service = CohortService(Cohort)


class AlgorithmService(BaseService[Algorithm, AlgorithmCreate, AlgorithmUpdate]):

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
            "[ALGORITHMS] GET to get_algorithms_by_cohort_list with cohort_ids: %s",
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

    def get_all_algorithm(self, db: Session) -> List[Algorithm]:
        """Return algorithms linked to a cohort."""
        logger.info("[ALGORITHMS] GET to get_all_algorithm")
        return db.query(Algorithm).options(joinedload(Algorithm.cohorts)).all()


algorithm_service = AlgorithmService(Algorithm)
