"""
Vantage6 integration service
Handles study registration and related orchestration
"""

from asyncio import tasks
import base64
import json
import requests
import time
import logging
import pandas as pd
import numpy as np

from app.models.workspace import Workspace
from app.models.algorithm import Algorithm
from app.models.cohort import Cohort
from datetime import datetime, timezone
from typing import Any, Optional, List
import httpx
import re

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.data_preparation import (
    CrosstabPreparationRequest,
    DataPreparationRequest,
    TTestRequest,
    BasicArithmeticRequest,
    V6TaskResult,
    V6RunResult,
    V6DecodedResult,
    V6Variables,
)
from app.schemas.workspace import (
    Workspace as WorkspaceSchema,
    WorkspaceUpdateVantage6Study,
    WorkspaceCreateV2,
)

# from vantage6.client import UserClient

from app.models.analysis import Analysis

from app.utils.constants import API_BASE, COLLABORATION_ID, ORGANIZATION_IDS, ALGORITHMS


class Vantage6Service(
    BaseService[Workspace, WorkspaceCreateV2, WorkspaceUpdateVantage6Study]
):
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url or API_BASE
        self.timeout = timeout

    def register_workspace(
        self,
        *,
        workspace_name: str,
        access_token: str,
    ) -> str:
        """
        Registra un workspace en Vantage6 y devuelve el v6_study_id.
        No requiere un objeto Workspace de la DB.
        """
        org_ids = self._get_org_ids(
            access_token=access_token, collaboration_id=COLLABORATION_ID
        )

        if not org_ids:
            raise RuntimeError("No organizations found for this collaboration")

        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        v6_name = self.generate_unique_workspace_name(workspace_name)

        payload = {
            "collaboration_id": COLLABORATION_ID,
            "organization_ids": org_ids,
            "name": v6_name,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        logger.debug("[V6] Payload to Vantage6: %s", json.dumps(payload, indent=2))

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/study", json=payload, headers=headers
                )
            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()
            data = response.json()
            logger.debug("[V6] Response from Vantage6: %s", json.dumps(data, indent=2))

            v6_study_id = (
                str(data.get("id"))
                if isinstance(data, dict) and "id" in data
                else str(data)
            )

            logger.debug("[V6] Response from Vantage6 v6_study_id: %s", v6_study_id)
            return str(data.get("id"))  # v6_study_id
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Vantage6 creation failed ({exc.response.status_code}): {exc.response.text}"
            )
        except httpx.RequestError as exc:
            raise RuntimeError(f"Cannot reach Vantage6: {str(exc)}")

    def generate_unique_workspace_name(self, base_name: str) -> str:
        # YYYYMMDD_HHMMSS por ejemplo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"

    def register_workspace2(
        self,
        db: Session,
        *,
        workspace: Workspace,
        access_token: str,
    ) -> Optional[Workspace]:
        """
        Registers a workspace in the external system.

        This method is intentionally side-effect oriented.
        It does NOT return the external representation.
        """
        logger.info("[V6] register_workspace START for workspace_id=%s", workspace.id)

        if not self.base_url:
            logger.warning("External workspace registry URL not configured")
            return

        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )
        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        if not org_ids:
            logger.warning(
                "Skipping Vantage6 registration for workspace %s: no organizations found",
                workspace.id,
            )
            return

        payload = {
            "collaboration_id": COLLABORATION_ID,
            "organization_ids": org_ids,
            "name": workspace.name,
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        logger.debug("[V6] Payload to Vantage6: %s", json.dumps(payload, indent=2))

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/study",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            data = response.json()
            logger.debug("[V6] Response from Vantage6: %s", json.dumps(data, indent=2))
            logger.info(
                "Workspace %s registered in Vantage6 successfully",
                workspace.id,
            )

            v6_study_id = (
                str(data.get("id"))
                if isinstance(data, dict) and "id" in data
                else str(data)
            )

            # Actualizar el workspace
            workspace_update = WorkspaceUpdateVantage6Study(
                v6_study_id=v6_study_id,
                last_modification_date=datetime.now(timezone.utc),
            )
            updated_workspace = self.update(
                db, db_obj=workspace, obj_in=workspace_update
            )

            logger.info(
                "[V6] Workspace %s updated in local DB with v6_study_id=%s",
                workspace.id,
                v6_study_id,
            )

            updated_workspace = self.update(
                db, db_obj=workspace, obj_in=workspace_update
            )
            return updated_workspace
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 study creation failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
            # decisión consciente: no romper flujo principal

        except httpx.RequestError as exc:
            logger.error("[V6] Failed to reach Vantage6: %s", str(exc))

        return None

    def _get_organizations(
        self,
        *,
        access_token: str,
        collaboration_id: int,
    ) -> dict[int, str]:
        """
        Returns organizations as {id: name}.
        """
        logger.info(
            "[V6] Fetching organizations from Vantage6 (collaboration_id=%s)",
            collaboration_id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/organization",
                    params={"collaboration_id": collaboration_id},
                    headers=headers,
                )

                response.raise_for_status()
                payload = response.json()
                organizations = {
                    org["id"]: org["name"] for org in payload.get("data", [])
                }

                # Temporary filter: only allow specific organizations (UPM and INT)

                organizations = {
                    org_id: name
                    for org_id, name in organizations.items()
                    if org_id in ORGANIZATION_IDS
                }

                logger.info(f"Organizations after filtering: {organizations}")
                return organizations
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))
        return {}

    # def _get_org_ids(self,*,access_token: str, collaboration_id: int) -> List[int]:
    #     """
    #     Obtiene las organizaciones asociadas a una colaboración ID.
    #     En producción → consultar la BBDD.
    #     """
    #     logger.info("[V6] _get_org_ids START for collaboration_id=%s", collaboration_id)
    #     if not self.base_url:
    #         logger.warning("[V6] External workspace registry URL not configured")
    #         return []

    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/json",
    #     }

    #     try:
    #         with httpx.Client(timeout=self.timeout) as client:
    #             response = client.get(
    #                 f"{self.base_url}/organization",
    #                 params={"collaboration_id": collaboration_id},
    #                 headers=headers,
    #             )

    #         logger.info("[V6] HTTP GET to %s returned status %s", response.url, response.status_code)
    #         response.raise_for_status()

    #         response_data = response.json()
    #         logger.debug("[V6] Full response data: %s", json.dumps(response_data, indent=2))

    #         data_list = response_data.get("data", [])
    #         ORGANIZATION_IDS = [org["id"] for org in data_list]
    #         logger.info("[V6] Extracted organization IDs: %s", ORGANIZATION_IDS)

    #         return ORGANIZATION_IDS
    #     except httpx.HTTPStatusError as exc:
    #         logger.error(
    #             "[V6] Vantage6 organization lookup failed (%s): %s",
    #             exc.response.status_code,
    #             exc.response.text,
    #         )

    #     except httpx.RequestError as exc:
    #         logger.error("[V6] Vantage6 unreachable: %s", str(exc))

    #     return []

    def _get_org_ids(
        self,
        *,
        access_token: str,
        collaboration_id: int,
    ) -> list[int]:
        return list(
            self._get_organizations(
                access_token=access_token,
                collaboration_id=collaboration_id,
            ).keys()
        )

    def _get_org_names(
        self,
        *,
        access_token: str,
        collaboration_id: int,
    ) -> list[str]:
        return list(
            self._get_organizations(
                access_token=access_token,
                collaboration_id=collaboration_id,
            ).values()
        )

    def create_new_session(
        self, *, access_token: str, workspace: Workspace, analysis: Analysis
    ) -> int:
        """
        Crea una nueva sesión en Vantage 6
        """
        logger.info(
            "[V6] _create_new_session START for collaboration_id=%s", COLLABORATION_ID
        )
        if not self.base_url:
            logger.warning("[V6] External session registry URL not configured")
            return -1

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "collaboration_id": COLLABORATION_ID,
            "name": f"{analysis.analysis_name}-{analysis.id}",
            "study_id": workspace.v6_study_id,
            "scope": "collaboration",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/session",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()
            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )
            v6_sesssion_id = (
                str(response_data.get("id"))
                if isinstance(response_data, dict) and "id" in response_data
                else str(response_data)
            )
            logger.info("[V6] Extracted session IDs: %s", v6_sesssion_id)

            return v6_sesssion_id
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return -1

    def create_new_cohort(
        self,
        *,
        access_token: str,
        session_id: int,
        features: str,
        patient_ids: List[Any] = None,
    ) -> int:
        """
        Crea una nuevo cohort en Vantage 6
        """
        IMAGE = "harbor2.vantage6.ai/idea4rc/sessions:latest"
        LABEL = "omop"
        METHOD = "create_cohort"

        logger.info("[V6] create_new_cohort START for session_id=%s", session_id)

        if not self.base_url:
            logger.warning("External cohort registry URL not configured")
            return

        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )
        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "patient_ids": patient_ids,
            "features": features,
        }

        logger.info("[V6] Arguments prepared create_new_cohort: %s", arguments)

        payload = {
            "label": LABEL,
            "task": {
                "method": METHOD,
                "image": IMAGE,
                "organizations": [
                    {
                        "id": id_,
                        "arguments": base64.b64encode(
                            json.dumps(arguments).encode("UTF-8")
                        ).decode("UTF-8"),
                    }
                    # We always create a cohort for all organizations in the study. Even though
                    # in a later stage we might send computation tasks to a subset of the
                    # organizations.
                    for id_ in org_ids
                ],
            },
        }

        logger.info(
            "[V6] Payload to send to Vantage6 to create cohort:\n%s",
            json.dumps(payload, indent=2),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/session/{session_id}/dataframe",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["last_session_task"]["id"]
            dataframe_id = response_data["id"]

            logger.info("[V6] Extracted dataframe_id IDs: %s", dataframe_id)

            with httpx.Client(timeout=self.timeout) as client:
                responseTask = client.get(
                    f"{self.base_url}/run?task_id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s",
                responseTask.url,
                responseTask.status_code,
            )
            responseTask.raise_for_status()

            responseTask_data = responseTask.json()

            logger.debug(
                "[V6] Full responseTask data: %s",
                json.dumps(responseTask_data, indent=2),
            )

            result = responseTask_data["data"][0]["status"]

            logger.info("[V6] Extracted result: %s", result)

            return dataframe_id
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return -1

    def data_preparation(
        self,
        db: Session,
        *,
        access_token: str,
        data_preparation_in: DataPreparationRequest,
    ) -> V6TaskResult:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """
        IMAGE = "harbor2.vantage6.ai/idea4rc/analytics:latest"
        METHOD = "summary"

        logger.info(
            "[V6] data_preparation START for data_preparation_in=%s",
            data_preparation_in,
        )

        if not self.base_url:
            logger.warning("External data_preparation  URL not configured")
            return

        # Verificar que el workspace existe
        workspace = (
            db.query(Workspace)
            .filter(Workspace.id == data_preparation_in.workspace_id)
            .first()
        )
        if not workspace:
            raise ValueError(
                f"Workspace with id {data_preparation_in.workspace_id} not found"
            )

        # Verificar que el analysis existe
        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == data_preparation_in.analysis_id)
            .first()
        )
        if not analysis:
            raise ValueError(
                f"Analysis with id {data_preparation_in.analysis_id} not found"
            )

        cohorts = (
            db.query(Cohort)
            .filter(Cohort.id.in_(data_preparation_in.cohorts_ids))
            .all()
        )
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        # 4️⃣ Extraer dataframe_vantage_id
        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        logger.info("[V6] workspace from db =%s", workspace)

        logger.info("[V6] analysis from db =%s", analysis)
        logger.info("[V6] cohorts from db =%s", dataframe_ids)
        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )

        org_NAMES = self._get_org_names(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )
        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        org_input = [
            {
                "id": org_ids[0],  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "organizations_to_include": org_ids,
                        }
                    ).encode("UTF-8")
                ).decode("UTF-8"),
            }
        ]

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": org_input,
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": analysis.session_id_vantage,
            "study_id": workspace.v6_study_id,
        }

        logger.info(
            "[V6] Payload to send to Vantage6:\n%s", json.dumps(payload, indent=2)
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/task",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            algorithm = Algorithm(
                method_name=ALGORITHMS.SUMMARY,
                description="Summary analysis",
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)
            logger.info("[V6] Extracted job_id IDs: %s", job_id)

            return V6TaskResult(
                task_id=task_id,
                job_id=job_id,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(
            task_id=-1,
            job_id=-1,
        )

    def create_crosstab(
        self,
        db: Session,
        *,
        access_token: str,
        crosstab_preparation_in: CrosstabPreparationRequest,
    ) -> V6TaskResult:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """
        IMAGE = "harbor2.vantage6.ai/idea4rc/analytics:latest"
        METHOD = "crosstab"

        logger.info(
            "[V6] create_crosstab START for crosstab_preparation_in=%s",
            crosstab_preparation_in,
        )

        if not self.base_url:
            logger.warning("External data_preparation  URL not configured")
            return

        # Verificar que el workspace existe
        workspace = (
            db.query(Workspace)
            .filter(Workspace.id == crosstab_preparation_in.workspace_id)
            .first()
        )
        if not workspace:
            raise ValueError(
                f"Workspace with id {crosstab_preparation_in.workspace_id} not found"
            )

        # Verificar que el analysis existe
        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == crosstab_preparation_in.analysis_id)
            .first()
        )
        if not analysis:
            raise ValueError(
                f"Analysis with id {crosstab_preparation_in.analysis_id} not found"
            )

        cohorts = (
            db.query(Cohort)
            .filter(Cohort.id.in_(crosstab_preparation_in.cohorts_ids))
            .all()
        )
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        # 4️⃣ Extraer dataframe_vantage_id
        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        logger.info("[V6] workspace from db =%s", workspace)

        logger.info("[V6] analysis from db =%s", analysis)
        logger.info("[V6] cohorts from db =%s", dataframe_ids)
        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )

        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        org_input = [
            {
                "id": org_ids[0],  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "results_col": crosstab_preparation_in.results_col,
                            "group_cols": crosstab_preparation_in.group_cols,
                            "organizations_to_include": org_ids,
                        }
                    ).encode("UTF-8")
                ).decode("UTF-8"),
            }
        ]

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": org_input,
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": analysis.session_id_vantage,
            "study_id": workspace.v6_study_id,
        }

        logger.info(
            "[V6] Payload to send to Vantage6 to create Crosstab:\n%s",
            json.dumps(payload, indent=2),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/task",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            # Create algorithm
            algorithm = Algorithm(
                method_name=ALGORITHMS.CROSSTABULATION,
                description="Crosstab analysis",
                input=json.dumps(crosstab_preparation_in.variablesList),
                col_var=crosstab_preparation_in.results_col,
                row_var_list=",".join(crosstab_preparation_in.group_cols),
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)

            logger.info("[V6] Extracted job_id IDs: %s", job_id)

            return V6TaskResult(
                task_id=task_id,
                job_id=job_id,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(
            task_id=-1,
            job_id=-1,
        )

    def create_t_test(
        self,
        db: Session,
        *,
        access_token: str,
        t_test_in: TTestRequest,
    ) -> V6TaskResult:
        """
        Crea un nuevo t-test en Vantage 6
        """
        IMAGE = "harbor2.vantage6.ai/idea4rc/analytics:latest"
        METHOD = "t_test_central"

        logger.info(
            "[V6] create_t_test START for t_test_in=%s",
            t_test_in,
        )

        if not self.base_url:
            logger.warning("External data_preparation  URL not configured")
            return

        # Verificar que el workspace existe
        workspace = (
            db.query(Workspace).filter(Workspace.id == t_test_in.workspace_id).first()
        )
        if not workspace:
            raise ValueError(f"Workspace with id {t_test_in.workspace_id} not found")

        # Verificar que el analysis existe
        analysis = (
            db.query(Analysis).filter(Analysis.id == t_test_in.analysis_id).first()
        )
        if not analysis:
            raise ValueError(f"Analysis with id {t_test_in.analysis_id} not found")

        cohorts = db.query(Cohort).filter(Cohort.id.in_(t_test_in.cohorts_ids)).all()
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        # 4️⃣ Extraer dataframe_vantage_id
        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        logger.info("[V6] workspace from db =%s", workspace)
        logger.info("[V6] analysis from db =%s", analysis)
        logger.info("[V6] cohorts from db =%s", dataframe_ids)
        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )

        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        org_input = [
            {
                "id": org_ids[0],  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "organizations_to_include": org_ids,
                        }
                    ).encode("UTF-8")
                ).decode("UTF-8"),
            }
        ]

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": org_input,
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": analysis.session_id_vantage,
            "study_id": workspace.v6_study_id,
        }

        logger.info(
            "[V6] Payload to send to Vantage6 to create T-test:\n%s",
            json.dumps(payload, indent=2),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/task",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            algorithm = Algorithm(
                method_name=ALGORITHMS.TTEST,
                description="T-test analysis",
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)

            logger.info("[V6] Extracted job_id IDs: %s", job_id)

            return V6TaskResult(
                task_id=task_id,
                job_id=job_id,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(
            task_id=-1,
            job_id=-1,
        )

    def get_variables_dataframe(
        self, *, access_token: str, dataframe_id: int
    ) -> V6Variables:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """

        logger.info(
            "[V6] get_variables_dataframe START for dataframe_id=%s", dataframe_id
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
                    f"{self.base_url}/session/dataframe/{dataframe_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            status_task = response_data["columns"]

            logger.debug("[V6]status_task: %s", json.dumps(status_task, indent=2))

            return V6Variables(
                variablesList=status_task,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6Variables(variablesList=[])

    def get_status_by_task_id(self, *, access_token: str, task_id: int) -> V6RunResult:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """

        logger.info("[V6] get_status_by_task_id START for task_id=%s", task_id)

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
                    f"{self.base_url}/run?task_id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            status_task = response_data["data"][0]["status"]

            return V6RunResult(
                status=status_task,
            )
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6RunResult(status="ERROR")

    def get_result_task_id(self, *, access_token: str, task_id: int) -> V6DecodedResult:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """

        logger.info("[V6] get_result_task_id START for task_id=%s", task_id)

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
                    f"{self.base_url}/result?task_id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()
            response_json = response.json()
            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_json, indent=2)
            )

            result_global = [
                json.loads(base64.b64decode(item["result"]).decode("UTF-8"))
                for item in response_json["data"]
            ]
            return V6DecodedResult(task_id=task_id, result=result_global[0])

        except (httpx.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.exception(
                "[V6] Error getting result for task_id=%s",
                task_id,
            )
            raise exc

    def get_subtasks(self, *, access_token: str, task_id: int) -> int:
        """
        Obtiene el ID de la subtask con method='summary_per_data_station'
        para una task padre en Vantage6.
        """

        logger.info("[V6] get_subtasks START for parent_task_id=%s", task_id)

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
                    f"{self.base_url}/task?parent_id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()
            response_json = response.json()
            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_json, indent=2)
            )

            tasks = response_json.get("data", [])
            if not isinstance(tasks, list):
                raise RuntimeError("Unexpected response format from Vantage6")

            for task in tasks:
                if task.get("method") == "summary_per_data_station":
                    subtask_id = task.get("id")
                    logger.info(
                        "[V6] Found subtask with method='summary_per_data_station', id=%s",
                        subtask_id,
                    )
                    return subtask_id

            raise RuntimeError(
                f"No subtask with method='summary_per_data_station' found for parent task {task_id}"
            )

        except (httpx.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.exception(
                "[V6] Error getting subtask for task_id=%s",
                task_id,
            )
            raise RuntimeError(f"Failed to retrieve subtask: {str(exc)}")

    def get_subtask_results(self, *, access_token: str, subtask_id: int) -> list[dict]:
        """
        Obtiene y decodifica los resultados de una subtask en Vantage6.
        Devuelve una lista de resultados ya decodificados (dict).
        """

        logger.info("[V6] get_task_results START for subtask_id=%s", subtask_id)

        if not self.base_url:
            raise RuntimeError("Vantage6 base_url not configured")

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/result?task_id={subtask_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s",
                response.url,
                response.status_code,
            )

            response.raise_for_status()

            response_json = response.json()

            logger.debug(
                "[V6] Full result response: %s",
                json.dumps(response_json, indent=2),
            )

            results = response_json.get("data", [])

            if not isinstance(results, list):
                raise RuntimeError("Unexpected result format from Vantage6")

            structured_results: dict[str, list] = {}

            for item in results:
                encoded_payload = item.get("result")
                if not encoded_payload:
                    continue

                decoded_json = json.loads(
                    base64.b64decode(encoded_payload).decode("UTF-8")
                )

                # decoded_json = { "mystifying_grothendieck": { ... } }

                for node_name, node_data in decoded_json.items():

                    if node_name not in structured_results:
                        structured_results[node_name] = []

                    structured_results[node_name].append(node_data)

            logger.info(
                "[V6] Successfully structured %s node(s)",
                len(structured_results),
            )

            return structured_results

        except (httpx.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.exception(
                "[V6] Error retrieving results for subtask_id=%s",
                subtask_id,
            )
            raise RuntimeError(f"Failed to retrieve task results: {str(exc)}")

    def create_basic_arithmetic(
        self,
        *,
        access_token: str,
        basic_arithmetic_in: BasicArithmeticRequest,
    ) -> V6TaskResult:
        """
        Executes a basic arithmetic preprocessing task in Vantage6.
        Modifies the specified dataframe in place by computing a new column.
        """
        IMAGE = "harbor2.vantage6.ai/idea4rc/preprocessing:latest"
        METHOD = "basic_arithmetic"

        logger.info(
            "[V6] create_basic_arithmetic START for dataframe_id=%s",
            basic_arithmetic_in.dataframe_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        org_ids = self._get_org_ids(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )

        logger.info("[V6] Organization IDs fetched: %s", org_ids)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column1": basic_arithmetic_in.column1,
            "column2": basic_arithmetic_in.column2,
            "operation": basic_arithmetic_in.operation,
            "output_column": basic_arithmetic_in.output_column,
        }

        payload = {
            "dataframe_id": basic_arithmetic_in.dataframe_id,
            "task": {
                "image": IMAGE,
                "method": METHOD,
                "organizations": [
                    {
                        "id": org_id,
                        "arguments": base64.b64encode(
                            json.dumps(arguments).encode("UTF-8")
                        ).decode("UTF-8"),
                    }
                    for org_id in org_ids
                ],
            },
        }

        logger.info(
            "[V6] Payload to send to Vantage6 for basic_arithmetic:\n%s",
            json.dumps(payload, indent=2),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/session/dataframe/{basic_arithmetic_in.dataframe_id}/preprocess",
                    json=payload,
                    headers=headers,
                )

            logger.info(
                "[V6] POST to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["last_session_task"]["id"]
            job_id = response_data["last_session_task"]["job_id"]

            return V6TaskResult(task_id=task_id, job_id=job_id)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 preprocessing failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(task_id=-1, job_id=-1)


vantage6_service = Vantage6Service()
