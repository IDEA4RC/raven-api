"""
Vantage6 integration service
Handles study registration and related orchestration
"""

from asyncio import tasks
import base64
import json
from app import db
from app.models import cohort
from app.models import algorithm
from app.models import workspace
import requests
import time
import logging
import pandas as pd
import numpy as np

from app.models.workspace import Workspace
from app.models.algorithm import Algorithm
from app.models.cohort import Cohort
from app.models.cohort_algorithm import CohortAlgorithm
from app.models.permit import Permit
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, List
import httpx
import re
import asyncio

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.services.base import BaseService
from app.schemas.data_preparation import (
    CrosstabPreparationRequest,
    DataPreparationRequest,
    TTestRequest,
    BasicArithmeticRequest,
    MergeCategoriesRequest,
    TimedeltaRequest,
    KaplanMeierRequest,
    OneHotEncodingRequest,
    GLMRequest,
    MergeVariablesRequest,
    CoxPHRequest,
    ToBooleanRequest,
    V6TaskResult,
    V6CreateDataFrame,
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

from app.utils.constants import (
    API_BASE,
    CENTRAL_TASK_ORG_ID,
    COE_CODE_ORG_ID_MAP,
    COLLABORATION_ID,
    ORGANIZATION_IDS,
    ALGORITHMS,
    PermitStatus,
)


class Vantage6Service(
    BaseService[Workspace, WorkspaceCreateV2, WorkspaceUpdateVantage6Study]
):
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url or API_BASE
        self.timeout = timeout

    def register_workspace(
        self,
        *,
        workspace_name: str,
        access_token: str,
        selected_coes: List[str],
    ) -> str:
        """
        Registra un workspace en Vantage6 y devuelve el v6_study_id.
        No requiere un objeto Workspace de la DB.
        """

        selected_org_ids = self.map_coe_codes_to_org_ids(selected_coes)

        logger.info(
            "[V6] Mapped selected COE codes %s to organization IDs: %s",
            selected_coes,
            selected_org_ids,
        )
        org_ids = list(
            self._get_online_organization_ids(
                access_token=access_token,
                collaboration_id=COLLABORATION_ID,
            )
        )

        logger.info(
            "[V6] org_ids from Colaboration ID %s: %s",
            COLLABORATION_ID,
            org_ids,
        )

        selected_set = set(selected_org_ids)
        org_ids = [oid for oid in org_ids if oid in selected_set]

        if CENTRAL_TASK_ORG_ID not in org_ids:
            org_ids.append(CENTRAL_TASK_ORG_ID)

        logger.info(
            "[V6] Create workspace in Vantage6 for selected orgs_id: %s", org_ids
        )
        if not org_ids:
            raise RuntimeError("No organizations found for this collaboration")

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

    # def register_workspace2(
    #     self,
    #     db: Session,
    #     *,
    #     workspace: Workspace,
    #     access_token: str,
    # ) -> Optional[Workspace]:
    #     """
    #     Registers a workspace in the external system.

    #     This method is intentionally side-effect oriented.
    #     It does NOT return the external representation.
    #     """
    #     logger.info("[V6] register_workspace START for workspace_id=%s", workspace.id)

    #     if not self.base_url:
    #         logger.warning("External workspace registry URL not configured")
    #         return

    #     org_ids = self._get_org_ids(
    #         access_token=access_token,
    #         collaboration_id=COLLABORATION_ID,
    #     )
    #     if not org_ids:
    #         logger.warning(
    #             "Skipping Vantage6 registration for workspace %s: no organizations found",
    #             workspace.id,
    #         )
    #         return

    #     payload = {
    #         "collaboration_id": COLLABORATION_ID,
    #         "organization_ids": org_ids,
    #         "name": workspace.name,
    #     }

    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/json",
    #     }

    #     try:
    #         with httpx.Client(timeout=self.timeout) as client:
    #             response = client.post(
    #                 f"{self.base_url}/study",
    #                 json=payload,
    #                 headers=headers,
    #             )

    #         logger.info(
    #             "[V6] POST to %s returned status %s", response.url, response.status_code
    #         )
    #         response.raise_for_status()

    #         data = response.json()

    #         v6_study_id = (
    #             str(data.get("id"))
    #             if isinstance(data, dict) and "id" in data
    #             else str(data)
    #         )

    #         # Actualizar el workspace
    #         workspace_update = WorkspaceUpdateVantage6Study(
    #             v6_study_id=v6_study_id,
    #             last_modification_date=datetime.now(timezone.utc),
    #         )
    #         updated_workspace = self.update(
    #             db, db_obj=workspace, obj_in=workspace_update
    #         )

    #         logger.info(
    #             "[V6] Workspace %s updated in local DB with v6_study_id=%s",
    #             workspace.id,
    #             v6_study_id,
    #         )

    #         updated_workspace = self.update(
    #             db, db_obj=workspace, obj_in=workspace_update
    #         )
    #         return updated_workspace
    #     except httpx.HTTPStatusError as exc:
    #         logger.error(
    #             "[V6] Vantage6 study creation failed (%s): %s",
    #             exc.response.status_code,
    #             exc.response.text,
    #         )
    #         # decisión consciente: no romper flujo principal

    #     except httpx.RequestError as exc:
    #         logger.error("[V6] Failed to reach Vantage6: %s", str(exc))

    #     return None

    def _get_online_organization_ids(
        self,
        *,
        access_token: str,
        collaboration_id: int,
    ) -> set[int]:
        """
        Returns the set of organization IDs that have an online node in the collaboration.
        """

        logger.info(
            "[V6 _get_online_organization_ids] Fetching online nodes for collaboration_id=%s",
            collaboration_id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/node",
                    params={"collaboration_id": collaboration_id, "per_page": 25},
                    headers=headers,
                )
                response.raise_for_status()
                nodes = response.json().get("data", [])
                online_from_nodes = {
                    node["organization"]["id"]
                    for node in nodes
                    if node.get("status") == "online"
                }

                orgs_with_nodes = {node["organization"]["id"] for node in nodes}

                logger.info(
                    "[V6_get_online_organization_ids] Online organization IDs: %s",
                    online_from_nodes,
                )

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

                org_ids = set(organizations.keys())

                orgs_without_nodes = org_ids - orgs_with_nodes
                final_ids = online_from_nodes | orgs_without_nodes

                logger.info(
                    "[V6_get_online_organization_ids] orgs_with_nodes=%s | orgs_without_nodes=%s | final=%s",
                    orgs_with_nodes,
                    orgs_without_nodes,
                    final_ids,
                )

                return final_ids
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6_get_online_organization_ids] Node lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error(
                "[V6_get_online_organization_ids] Vantage6 unreachable fetching nodes: %s",
                str(exc),
            )
        return set()

    def _get_organizations(
        self,
        *,
        access_token: str,
        collaboration_id: int,
    ) -> dict[int, str]:
        """
        Returns organizations as {id: name}. have an online node in Vantage6.
        """
        logger.info(
            "[V6_get_organizations] Fetching organizations from Vantage6 (collaboration_id=%s)",
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

            logger.info(
                "[V6_get_organizations] All organizations: %s after API fetch %s",
                organizations,
                "%s/organization?collaboration_id=%s",
                self.base_url,
                collaboration_id,
            )

            online_ids = self._get_online_organization_ids(
                access_token=access_token,
                collaboration_id=collaboration_id,
            )

            organizations = {
                org_id: name
                for org_id, name in organizations.items()
                if org_id in ORGANIZATION_IDS and org_id in online_ids
            }

            logger.info(
                "[V6_get_organizations] Organizations after filtering: %s",
                organizations,
            )
            return organizations

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6_get_organizations] Organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error(
                "[V6_get_organizations] Vantage6 unreachable: %s",
                str(exc),
            )
        return {}

    def get_available_organizations(
        self,
        *,
        access_token: str,
    ) -> list[dict]:
        """
        Returns the list of organizations available for task submission.
        Each entry has {id, name}.
        """
        orgs = self._get_organizations(
            access_token=access_token,
            collaboration_id=COLLABORATION_ID,
        )
        return [{"id": org_id, "name": name} for org_id, name in orgs.items()]

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
    #

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

    # def _get_study_org_ids(
    #     self,
    #     *,
    #     access_token: str,
    #     study_id,
    # ) -> set[int]:
    #     """Returns the set of organization IDs that belong to the given V6 study."""
    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/json",
    #     }
    #     try:
    #         with httpx.Client(timeout=self.timeout) as client:
    #             response = client.get(
    #                 f"{self.base_url}/organization",
    #                 params={"study_id": study_id},
    #                 headers=headers,
    #             )
    #             response.raise_for_status()
    #             data = response.json()
    #             org_ids = {org["id"] for org in data.get("data", [])}
    #             return org_ids
    #     except httpx.HTTPStatusError as exc:
    #         logger.error(
    #             "[V6] Study org lookup failed for study %s (%s): %s",
    #             study_id,
    #             exc.response.status_code,
    #             exc.response.text,
    #         )
    #     except httpx.RequestError as exc:
    #         logger.error("[V6] Vantage6 unreachable fetching study orgs: %s", str(exc))
    #     return set()

    def _get_orgs_with_dataframe(
        self, *, access_token: str, dataframe_id: int
    ) -> set[int]:
        """Returns org IDs whose nodes have the given dataframe present."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                df_response = client.get(
                    f"{self.base_url}/session/dataframe/{dataframe_id}",
                    headers=headers,
                )
                df_response.raise_for_status()
                df_data = df_response.json()
                columns = df_data.get("columns", [])
                if columns:
                    sample = columns[0]
                node_ids = set()
                for col in columns:
                    if not isinstance(col, dict):
                        continue
                    nid = col.get("node_id") or col.get("node")
                    if isinstance(nid, dict):
                        nid = nid.get("id")
                    if nid is not None:
                        node_ids.add(int(nid))

                if not node_ids:
                    logger.warning(
                        "[V6] Could not extract node IDs from dataframe %s columns — dataframe filter skipped",
                        dataframe_id,
                    )
                    return set()

                node_response = client.get(
                    f"{self.base_url}/node",
                    params={"collaboration_id": COLLABORATION_ID},
                    headers=headers,
                )
                node_response.raise_for_status()
                nodes = node_response.json().get("data", [])
                org_ids = {
                    node["organization"]["id"]
                    for node in nodes
                    if node.get("id") in node_ids
                }

                return org_ids
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Dataframe org lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable fetching dataframe orgs: %s", exc)
        return set()

    def _get_org_ids(
        self,
        *,
        access_token: str,
        db: Session,
        workspace_id: int,
    ) -> list[int]:

        org_ids = list(
            self._get_online_organization_ids(
                access_token=access_token,
                collaboration_id=COLLABORATION_ID,
            )
        )

        logger.info(
            "[V6] Initial org IDs for collaboration_id=%s: %s",
            COLLABORATION_ID,
            org_ids,
        )

        authorized_org_ids = None
        authorized_org_ids = self._get_authorized_org_ids(
            db=db,
            workspace_id=workspace_id,
        )

        logger.info(
            "[V6]  authorized_org_ids IDs for worskpace_id=%s: %s",
            workspace_id,
            authorized_org_ids,
        )

        if authorized_org_ids is not None:
            org_ids = [oid for oid in org_ids if oid in authorized_org_ids]

        logger.info(
            "[V6] Final org ids:  %s",
            org_ids,
        )

        return org_ids

    def _get_study_id_for_dataframe(
        self, db: Session, dataframe_id: int, access_token: str = None
    ):
        """Returns v6_study_id for the workspace that owns the given dataframe.
        Primary: DB lookup via cohort → workspace.
        Fallback: V6 API lookup via dataframe → session → study.
        """
        cohort = (
            db.query(Cohort).filter(Cohort.dataframe_vantage_id == dataframe_id).first()
        )
        if cohort:
            workspace = (
                db.query(Workspace).filter(Workspace.id == cohort.workspace_id).first()
            )
            if workspace and workspace.v6_study_id:

                return workspace.v6_study_id

        else:
            logger.warning(
                "[V6] No cohort found in DB for dataframe_vantage_id=%s — trying V6 fallback",
                dataframe_id,
            )

        if access_token:
            study_id = self._get_study_id_from_v6(
                access_token=access_token, dataframe_id=dataframe_id
            )
            if study_id:
                return study_id

        logger.error(
            "[V6] Could not determine study_id for dataframe %s — org filter will be skipped",
            dataframe_id,
        )
        return None

    def _get_study_id_from_v6(self, *, access_token: str, dataframe_id: int):
        """Fallback: get study_id for a dataframe via V6 API chain:
        GET /session/dataframe/{id} → session_id → GET /session/{id} → study_id
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                df_response = client.get(
                    f"{self.base_url}/session/dataframe/{dataframe_id}",
                    headers=headers,
                )
                df_response.raise_for_status()
                df_data = df_response.json()

                # Extract session_id — handle both flat and nested V6 responses
                session_id = df_data.get("session_id")
                if not session_id:
                    session_obj = df_data.get("session")
                    if isinstance(session_obj, dict):
                        session_id = session_obj.get("id")
                    elif isinstance(session_obj, (int, str)):
                        session_id = session_obj

                if not session_id:
                    logger.warning(
                        "[V6] Could not extract session_id from dataframe %s response",
                        dataframe_id,
                    )
                    return None

                session_response = client.get(
                    f"{self.base_url}/session/{session_id}",
                    headers=headers,
                )
                session_response.raise_for_status()
                session_data = session_response.json()

                # Extract study_id — handle both flat and nested
                study_id = session_data.get("study_id")
                if not study_id:
                    study_obj = session_data.get("study")
                    if isinstance(study_obj, dict):
                        study_id = study_obj.get("id")
                    elif isinstance(study_obj, (int, str)):
                        study_id = study_obj

                if study_id:

                    return str(study_id)

                logger.warning(
                    "[V6] Could not extract study_id from session %s response",
                    session_id,
                )
                return None

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] V6 fallback study lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error("[V6] V6 fallback study lookup unreachable: %s", exc)
        return None

    @staticmethod
    def _parse_missing_dataframe_orgs(error_msg: str) -> set[int]:
        """Extract org IDs from V6 error 'not present for the following organizations: X, Y'."""
        match = re.search(
            r"not present for the following organizations:\s*([\d,\s]+)", error_msg
        )
        if match:
            return {
                int(x.strip()) for x in match.group(1).split(",") if x.strip().isdigit()
            }
        return set()

    def _post_preprocess_with_retry(self, *, client, dataframe_id, payload, headers):
        """POST to /session/dataframe/{id}/preprocess, retrying once without orgs that lack the dataframe."""
        url = f"{self.base_url}/session/dataframe/{dataframe_id}/preprocess"
        response = client.post(url, json=payload, headers=headers)
        logger.info("[V6] POST to %s returned status %s", url, response.status_code)
        if response.status_code == 400:
            bad_orgs = self._parse_missing_dataframe_orgs(
                response.json().get("msg", "")
            )
            if bad_orgs:
                remaining = [
                    o
                    for o in payload["task"]["organizations"]
                    if o["id"] not in bad_orgs
                ]
                if remaining:
                    logger.warning(
                        "[V6] Retrying preprocess without orgs %s (dataframe not present)",
                        bad_orgs,
                    )
                    payload = {
                        **payload,
                        "task": {**payload["task"], "organizations": remaining},
                    }
                    response = client.post(url, json=payload, headers=headers)
                    logger.info(
                        "[V6] Retry POST to %s returned status %s",
                        url,
                        response.status_code,
                    )
        return response

    def _post_task_with_retry(self, *, client, payload, headers, org_arg_key):
        """POST to /task, retrying once without orgs that lack the required dataframe."""
        url = f"{self.base_url}/task"
        response = client.post(url, json=payload, headers=headers)
        logger.info("[V6] POST to %s returned status %s", url, response.status_code)
        if response.status_code == 400:
            bad_orgs = self._parse_missing_dataframe_orgs(
                response.json().get("msg", "")
            )
            if bad_orgs:
                payload = json.loads(json.dumps(payload))  # deep copy
                for org in payload["organizations"]:
                    args = json.loads(base64.b64decode(org["arguments"]))
                    if org_arg_key in args:
                        args[org_arg_key] = [
                            o for o in args[org_arg_key] if o not in bad_orgs
                        ]
                        org["arguments"] = base64.b64encode(
                            json.dumps(args).encode()
                        ).decode()
                # If the central task org itself is bad, replace its ID with first remaining good org
                central = payload["organizations"][0]
                if central["id"] in bad_orgs:
                    args = json.loads(base64.b64decode(central["arguments"]))
                    valid_orgs = args.get(org_arg_key, [])
                    if not valid_orgs:
                        logger.error(
                            "[V6] No valid orgs left after dataframe filter — cannot retry task"
                        )
                        return response
                    central["id"] = valid_orgs[0]
                    central["arguments"] = base64.b64encode(
                        json.dumps(args).encode()
                    ).decode()
                logger.warning(
                    "[V6] Retrying task without orgs %s (dataframe not present)",
                    bad_orgs,
                )
                response = client.post(url, json=payload, headers=headers)
                logger.info(
                    "[V6] Retry POST to %s returned status %s",
                    url,
                    response.status_code,
                )
        return response

    def _get_session_org_ids(self, *, access_token: str, session_id) -> set[int]:
        """Returns the set of organization IDs that belong to the given V6 session."""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    f"{self.base_url}/organization",
                    params={"session_id": session_id},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                org_ids = {org["id"] for org in data.get("data", [])}
                logger.info("[V6] Session %s organization IDs: %s", session_id, org_ids)
                return org_ids
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Session org lookup failed for session %s (%s): %s",
                session_id,
                exc.response.status_code,
                exc.response.text,
            )
        except httpx.RequestError as exc:
            logger.error(
                "[V6] Vantage6 unreachable fetching session orgs: %s", str(exc)
            )
        return set()

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
        db: Session,
        *,
        access_token: str,
        session_id: int,
        features: str,
        patient_ids_by_org: dict,
        workspace_id: int,
    ) -> V6CreateDataFrame:
        """
        Crea una nuevo cohort en Vantage 6
        """
        IMAGE = "ghcr.io/iknl/sessions:latest"
        LABEL = "omop"
        METHOD = "create_cohort"

        logger.info("[V6] create_new_cohort START for workspace_id=%s", workspace_id)

        if not self.base_url:
            logger.warning("External cohort registry URL not configured")
            return

        org_ids = self._get_org_ids_create_cohort(
            access_token=access_token,
            db=db,
            workspace_id=workspace_id,
        )

        logger.info("[V6] Retrieved organization IDs for cohort creation: %s", org_ids)

        # logger.info("[V6] Patients IDs for cohort creation: %s", patient_ids_by_org)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        patient_ids_by_org = patient_ids_by_org or {}

        # Only include orgs that are both in the study (org_ids) and have patient data
        orgs_to_include = [oid for oid in org_ids if oid in patient_ids_by_org]
        logger.info("[V6] Orgs Retrieved SECOND TIME: %s", patient_ids_by_org)

        logger.info("[V6] features: %s", features)
        logger.info("[V6] Orgs to include in cohort creation: %s", orgs_to_include)
        payload = {
            "label": LABEL,
            "task": {
                "method": METHOD,
                "image": IMAGE,
                "organizations": [
                    {
                        "id": org_id,
                        "arguments": base64.b64encode(
                            json.dumps(
                                {
                                    "patient_ids": patient_ids_by_org[org_id],
                                    "features": features,
                                }
                            ).encode("UTF-8")
                        ).decode("UTF-8"),
                    }
                    for org_id in orgs_to_include
                ],
            },
        }

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

            task_id = response_data["last_session_task"]["id"]
            dataframe_id = response_data["id"]

            logger.info(
                "[V6] Extracted dataframe_id IDs: %s task_id: %s",
                dataframe_id,
                task_id,
            )

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

            result = responseTask_data["data"][0]["status"]

            logger.info("[V6] Cohort creation task status: %s", result)

            return V6CreateDataFrame(task_id=task_id, dataframe_id=dataframe_id)
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6CreateDataFrame(task_id=-1, dataframe_id=-1)

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
        IMAGE = "ghcr.io/iknl/analytics:latest"
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

        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        logger.info(
            "[V6] data_preparation: dataframe_ids: %s ",
            dataframe_ids,
        )

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]

        logger.info(
            "[V6] data_preparation: orgs_ids: %s and orgs_ids_to_include: %s",
            org_ids,
            org_to_include,
        )

        org_input = [
            {
                "id": central_task,  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "organizations_to_include": org_to_include,
                        }
                    ).encode("UTF-8")
                ).decode("UTF-8"),
            }
        ]

        logger.info("[V6] data_preparation: org_input: %s ", org_input)

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

        logger.info("[V6] data_preparation: payload: %s ", payload)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()

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
        IMAGE = "ghcr.io/iknl/analytics:latest"
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

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        org_input = [
            {
                "id": central_task,  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "results_col": crosstab_preparation_in.results_col,
                            "group_cols": crosstab_preparation_in.group_cols,
                            "organizations_to_include": org_to_include,
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

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()

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
        IMAGE = "ghcr.io/iknl/analytics:latest"
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

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]

        org_input = [
            {
                "id": central_task,  # Central task
                "arguments": base64.b64encode(
                    json.dumps(
                        {
                            "organizations_to_include": org_to_include,
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

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()

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

            status_task = response_data["columns"]

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

            status_task = response_data["data"][0]["status"]

            return V6RunResult(
                status=status_task,
                logs=response_data["data"][0].get("log", ""),
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

    def get_task_status_with_timeout(
        self,
        db: Session,
        *,
        access_token: str,
        task_id: int,
        timeout_minutes: int = 5,
    ) -> Any:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """

        logger.info("[V6] get_task_status_with_timeout START for task_id=%s", task_id)

        algorithm = db.query(Algorithm).filter(Algorithm.task_id == task_id).first()
        if not algorithm:
            raise ValueError(f"Algorithm with task_id {task_id} not found")

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

            data = response.json().get("data", [])

            if not data:
                return None

            task = data[0]

            now = datetime.utcnow()
            started_at = task.get("started_at")
            finished_at = task.get("finished_at")

            # parse ISO dates safely
            def parse(dt):
                if not dt:
                    return None
                try:
                    return datetime.fromisoformat(dt.replace("Z", ""))
                except Exception:
                    return None

            start_dt = parse(started_at)

            algorithm.finished_at = finished_at
            algorithm.started_at = started_at
            algorithm.status_task = task.get("status")
            if start_dt and not finished_at:
                elapsed = now - start_dt

                if elapsed > timedelta(minutes=timeout_minutes):
                    logger.warning(
                        "[V6] Task %s exceeded timeout (%s min). Marking as killed.",
                        task_id,
                        timeout_minutes,
                    )
                    algorithm.status_task = "killed_by_user_timeout"

                    task["status"] = "killed_by_user_timeout"
                    task["client_timeout_at"] = now.isoformat()

            db.add(algorithm)
            db.commit()
            return task["status"]

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return None

    async def update_algorithms_status_bulk_async(
        self, db: Session, algorithms: List[Algorithm], access_token: str
    ) -> List[Algorithm]:

        logger.info("[V6] Async bulk update for %s algorithms", len(algorithms))

        async with httpx.AsyncClient(timeout=self.timeout) as client:

            tasks = [
                self.fetch_algorithm_status(client, access_token, alg)
                for alg in algorithms
            ]

            results = await asyncio.gather(*tasks)

        # 🔥 aplicar resultados (SECUENCIAL DB SAFE)
        updated_algorithms = []

        for algorithm, data in results:
            if data:
                algorithm.started_at = data["started_at"]
                algorithm.finished_at = data["finished_at"]
                algorithm.status = data["status"]
                updated_algorithms.append(algorithm)

        db.commit()

        for alg in updated_algorithms:
            db.refresh(alg)

        return updated_algorithms

    async def fetch_algorithm_status(
        self, client: httpx.AsyncClient, access_token: str, algorithm: Algorithm
    ):
        task_id = algorithm.task_id

        try:
            response = await client.get(
                f"{self.base_url}/run?task_id={task_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
            )

            response.raise_for_status()
            data = response.json().get("data", [])

            if not data:
                return algorithm, None

            run_data = data[0]

            return algorithm, {
                "started_at": run_data.get("started_at"),
                "finished_at": run_data.get("finished_at"),
                "status": run_data.get("status"),
            }

        except Exception as e:
            logger.error("[V6] Error fetching task %s: %s", task_id, str(e))
            return algorithm, None

    def update_algorithm_status_by_task_id(
        self, db: Session, *, access_token: str, algorithm: Algorithm
    ) -> Algorithm:
        """
        Crea un nuevo data data_preparation en Vantage 6
        """

        task_id = algorithm.task_id
        logger.info(
            "[V6] update_algorithm_status_by_task_id START for task_id=%s",
            algorithm.task_id,
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
                    f"{self.base_url}/run?task_id={task_id}",
                    headers=headers,
                )

            logger.info(
                "[V6] GET to %s returned status %s", response.url, response.status_code
            )
            response.raise_for_status()

            response_data = response.json()
            data = response_data.get("data", [])

            if not data:
                logger.warning("[V6] No run data for task_id=%s", task_id)
                return None

            run_data = data[0]
            algorithm.started_at = run_data["started_at"]
            if run_data["finished_at"]:
                algorithm.finished_at = run_data["finished_at"]
            algorithm.status_task = run_data["status"]

            return algorithm
        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 organization lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return None

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

            data = response_json.get("data", [])
            if not data:
                raise ValueError(f"No result data for task_id={task_id}")

            item = data[0]
            raw_result = item.get("result")
            if raw_result:
                decoded = json.loads(base64.b64decode(raw_result).decode("UTF-8"))
                return V6DecodedResult(task_id=task_id, result=decoded)

            log = item.get("log") or "No result and no log available"
            return V6DecodedResult(task_id=task_id, result={"error": log})

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

            tasks = response_json.get("data", [])
            if not isinstance(tasks, list):
                raise RuntimeError("Unexpected response format from Vantage6")

            return [
                {
                    "id": t.get("id"),
                    "method": t.get("method"),
                    "status": t.get("status"),
                }
                for t in tasks
            ]

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
            results = response_json.get("data", [])

            if not isinstance(results, list):
                raise RuntimeError("Unexpected result format from Vantage6")

            structured_results: dict[str, list] = {}

            for item in results:
                encoded_payload = item.get("result")
                if not encoded_payload:
                    log = item.get("log")
                    if log:
                        structured_results["_log"] = structured_results.get("_log", [])
                        structured_results["_log"].append(log)
                    continue

                decoded_json = json.loads(
                    base64.b64decode(encoded_payload).decode("UTF-8")
                )

                for node_name, node_data in decoded_json.items():

                    if node_name not in structured_results:
                        structured_results[node_name] = []

                    structured_results[node_name].append(node_data)

            if not structured_results:
                return {"error": "No result available for this subtask"}

            return structured_results

        except (httpx.HTTPError, ValueError, json.JSONDecodeError, KeyError) as exc:
            logger.exception(
                "[V6] Error retrieving results for subtask_id=%s",
                subtask_id,
            )
            raise RuntimeError(f"Failed to retrieve task results: {str(exc)}")

    def create_coxph(
        self,
        db: Session,
        *,
        access_token: str,
        coxph_in: CoxPHRequest,
    ) -> V6TaskResult:
        """
        Executes a Cox Proportional Hazards (CoxPH) analytics task in Vantage6.
        """
        IMAGE = "ghcr.io/iknl/analytics:latest"
        METHOD = "coxph_central"

        logger.info("[V6] create_coxph START for coxph_in=%s", coxph_in)

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        workspace = (
            db.query(Workspace).filter(Workspace.id == coxph_in.workspace_id).first()
        )
        if not workspace:
            raise ValueError(f"Workspace with id {coxph_in.workspace_id} not found")

        analysis = (
            db.query(Analysis).filter(Analysis.id == coxph_in.analysis_id).first()
        )
        if not analysis:
            raise ValueError(f"Analysis with id {coxph_in.analysis_id} not found")

        cohorts = db.query(Cohort).filter(Cohort.id.in_(coxph_in.cohorts_ids)).all()
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]

        arguments = {
            "organizations_to_include": list(org_to_include),
            "time_col": coxph_in.time_col,
            "outcome_col": coxph_in.outcome_col,
            "expl_vars": coxph_in.expl_vars,
        }

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": [
                {
                    "id": central_task,
                    "arguments": base64.b64encode(
                        json.dumps(arguments).encode("UTF-8")
                    ).decode("UTF-8"),
                }
            ],
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
            "[V6] Payload to send to Vantage6 for coxph:\n%s",
            json.dumps(payload, indent=2),
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            columns = coxph_in.expl_vars + [coxph_in.time_col, coxph_in.outcome_col]

            algorithm = Algorithm(
                method_name=ALGORITHMS.COXPH,
                description="Cox Proportional Hazards model",
                input=json.dumps(columns),
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)

            return V6TaskResult(task_id=task_id, job_id=job_id)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 coxph failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(task_id=-1, job_id=-1)

    def create_glm(
        self,
        db: Session,
        *,
        access_token: str,
        glm_in: GLMRequest,
    ) -> V6TaskResult:
        """
        Executes a Generalized Linear Model (GLM) analytics task in Vantage6.
        """
        IMAGE = "ghcr.io/iknl/analytics:latest"
        METHOD = "glm"

        logger.info("[V6] create_glm START for glm_in=%s", glm_in)

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        workspace = (
            db.query(Workspace).filter(Workspace.id == glm_in.workspace_id).first()
        )
        if not workspace:
            raise ValueError(f"Workspace with id {glm_in.workspace_id} not found")

        analysis = db.query(Analysis).filter(Analysis.id == glm_in.analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis with id {glm_in.analysis_id} not found")

        cohorts = db.query(Cohort).filter(Cohort.id.in_(glm_in.cohorts_ids)).all()
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "organizations_to_include": org_to_include,
            "family": glm_in.family,
            "predictor_variables": glm_in.predictor_variables,
            "outcome_variable": glm_in.outcome_variable,
        }

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": [
                {
                    "id": central_task,
                    "arguments": base64.b64encode(
                        json.dumps(arguments).encode("UTF-8")
                    ).decode("UTF-8"),
                }
            ],
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": analysis.session_id_vantage,
            "study_id": workspace.v6_study_id,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()

            logger.info(
                "[V6] Response from Vantage6 for GLM task creation status: %s, message: %s",
                response.status_code,
                response.text,
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            columns = glm_in.predictor_variables + [glm_in.outcome_variable]

            algorithm = Algorithm(
                method_name=ALGORITHMS.GLM,
                description="Generalized Linear Model",
                input=json.dumps(columns),
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)

            return V6TaskResult(task_id=task_id, job_id=job_id)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 glm failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(task_id=-1, job_id=-1)

    def create_kaplan_meier(
        self,
        db: Session,
        *,
        access_token: str,
        km_in: KaplanMeierRequest,
    ) -> V6TaskResult:
        """
        Executes a Kaplan-Meier survival analysis task in Vantage6.
        Returns both the KM estimate and the Log-Rank test in a single response.
        """
        IMAGE = "ghcr.io/iknl/analytics:latest"
        METHOD = "kaplan_meier_central"

        logger.info(
            "[V6] create_kaplan_meier START for km_in=%s",
            km_in,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        workspace = (
            db.query(Workspace).filter(Workspace.id == km_in.workspace_id).first()
        )
        if not workspace:
            raise ValueError(f"Workspace with id {km_in.workspace_id} not found")

        analysis = db.query(Analysis).filter(Analysis.id == km_in.analysis_id).first()
        if not analysis:
            raise ValueError(f"Analysis with id {km_in.analysis_id} not found")

        cohorts = db.query(Cohort).filter(Cohort.id.in_(km_in.cohorts_ids)).all()
        if not cohorts:
            raise ValueError("No cohorts found for the provided IDs")

        dataframe_ids = [
            cohort.dataframe_vantage_id
            for cohort in cohorts
            if cohort.dataframe_vantage_id is not None
        ]

        org_ids = self._get_org_ids(
            access_token=access_token,
            db=db,
            workspace_id=workspace.id,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        central_task = CENTRAL_TASK_ORG_ID
        org_to_include = [oid for oid in org_ids if oid != central_task]
        arguments = {
            "organizations_to_include": org_to_include,
            "time_column_name": km_in.time_column_name,
            "censor_column_name": km_in.censor_column_name,
        }
        if km_in.strata_column_name is not None:
            arguments["strata_column_name"] = km_in.strata_column_name

        payload = {
            "name": "Human-readable name of the task",
            "image": IMAGE,
            "description": "Description of the task",
            "action": "central_compute",
            "method": METHOD,
            "organizations": [
                {
                    "id": central_task,  # Central task
                    "arguments": base64.b64encode(
                        json.dumps(arguments).encode("UTF-8")
                    ).decode("UTF-8"),
                }
            ],
            "databases": [
                [
                    {"type": "dataframe", "dataframe_id": df_id}
                    for df_id in dataframe_ids
                ]
            ],
            "session_id": analysis.session_id_vantage,
            "study_id": workspace.v6_study_id,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = self._post_task_with_retry(
                    client=client,
                    payload=payload,
                    headers=headers,
                    org_arg_key="organizations_to_include",
                )
            response.raise_for_status()

            response_data = response.json()
            logger.info(
                "[V6] GET create_kaplan_meier to %s returned status %s",
                response.url,
                response.status_code,
            )

            logger.debug(
                "[V6] Full response data: %s", json.dumps(response_data, indent=2)
            )

            task_id = response_data["id"]
            job_id = response_data["job_id"]

            columns = [km_in.time_column_name, km_in.censor_column_name]
            if km_in.strata_column_name:
                columns.append(km_in.strata_column_name)

            algorithm = Algorithm(
                method_name=ALGORITHMS.KAPLAN_MEIER,
                description="Kaplan-Meier survival analysis",
                input=json.dumps(columns),
                task_id=task_id,
            )

            algorithm.cohorts = cohorts

            db.add(algorithm)
            db.commit()
            db.refresh(algorithm)

            return V6TaskResult(task_id=task_id, job_id=job_id)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "[V6] Vantage6 kaplan_meier failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )

        except httpx.RequestError as exc:
            logger.error("[V6] Vantage6 unreachable: %s", str(exc))

        return V6TaskResult(task_id=-1, job_id=-1)

    def create_basic_arithmetic(
        self,
        db: Session,
        *,
        access_token: str,
        basic_arithmetic_in: BasicArithmeticRequest,
    ) -> V6TaskResult:
        """
        Executes a basic arithmetic preprocessing task in Vantage6.
        Modifies the specified dataframe in place by computing a new column.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "basic_arithmetic"

        logger.info(
            "[V6] create_basic_arithmetic START for analysis_id=%s",
            basic_arithmetic_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == basic_arithmetic_in.analysis_id)
            .first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )

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

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:
                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    payload = {
                        "dataframe_id": df_id,
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

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )
                    response.raise_for_status()

                    response_data = response.json()
                    logger.info(
                        "[V6] GET create_basic_arithmetic to %s returned status %s",
                        response.url,
                        response.status_code,
                    )

                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]
                    self.update_cohort_task_id(
                        db=db, dataframe_id=df_id, task_id=task_id
                    )
                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))

            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )

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

    def create_merge_categories(
        self,
        db: Session,
        *,
        access_token: str,
        merge_categories_in: MergeCategoriesRequest,
    ) -> V6TaskResult:
        """
        Executes a merge_categories preprocessing task in Vantage6.
        Remaps categories of an existing column into a new output column.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "merge_categories"

        logger.info(
            "[V6] create_merge_categories START for analysis_id=%s",
            merge_categories_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        # org_ids = self._get_org_ids_with_dataframe(
        #     access_token=access_token,
        #     dataframe_id=merge_categories_in.dataframe_id,
        # )

        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == merge_categories_in.analysis_id)
            .first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column": merge_categories_in.column,
            "output_column": merge_categories_in.output_column,
            "mapping": merge_categories_in.mapping,
        }

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:

                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    payload = {
                        "dataframe_id": df_id,
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
                        "[V6] Payload to send to Vantage6 for merge_categories:\n%s",
                        json.dumps(payload, indent=2),
                    )

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )

                    response.raise_for_status()

                    response_data = response.json()
                    logger.info(
                        "[V6] GET create_merge_categories to %s returned status %s",
                        response.url,
                        response.status_code,
                    )
                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]
                    self.update_cohort_task_id(
                        db=db, dataframe_id=df_id, task_id=task_id
                    )

                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))
            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )

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

    def create_timedelta(
        self,
        db: Session,
        *,
        access_token: str,
        timedelta_in: TimedeltaRequest,
    ) -> V6TaskResult:
        """
        Executes a timedelta preprocessing task in Vantage6.
        Computes the number of days from a date column to today and stores it in output_column.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "timedelta"

        logger.info(
            "[V6] create_timedelta START for analysis_id=%s",
            timedelta_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        # org_ids = self._get_org_ids_with_dataframe(
        #     access_token=access_token,
        #     dataframe_id=timedelta_in.dataframe_id,
        # )

        analysis = (
            db.query(Analysis).filter(Analysis.id == timedelta_in.analysis_id).first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column": timedelta_in.column,
            "output_column": timedelta_in.output_column,
        }

        if timedelta_in.to_date_column:
            arguments["to_date_column"] = timedelta_in.to_date_column
        elif timedelta_in.to_date:
            try:
                datetime.strptime(timedelta_in.to_date, "%Y-%m-%d")
            except ValueError:
                raise httpx.HTTPStatusError(
                    status_code=400, detail="to_date must be in format YYYY-MM-DD"
                )
            arguments["to_date"] = timedelta_in.to_date

        # logger.info(
        #     "[V6] Running timedelta with arguments=%s", json.dumps(arguments, indent=2)
        # )

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:

                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    logger.info("[V6] TIMEDELTA: Organization IDs fetched: %s", org_ids)
                    payload = {
                        "dataframe_id": df_id,
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
                        "[V6] Payload to send to Vantage6 for timedelta:\n%s",
                        json.dumps(payload, indent=2),
                    )

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )

                    response.raise_for_status()

                    response_data = response.json()

                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]

                    logger.info(
                        "[V6] Extracted task_id TIMEDELTACREATION: %s, job_id: %s",
                        task_id,
                        job_id,
                    )

                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))
                    self.update_cohort_task_id(
                        db=db, dataframe_id=df_id, task_id=task_id
                    )

            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )

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

    def create_to_boolean(
        self,
        db: Session,
        *,
        access_token: str,
        to_boolean_in: ToBooleanRequest,
    ) -> V6TaskResult:
        """
        Executes a to_boolean preprocessing task in Vantage6.
        Converts a categorical column to boolean based on the provided true_values.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "to_boolean"

        logger.info(
            "[V6] create_to_boolean START for analysis_id=%s",
            to_boolean_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        # org_ids = self._get_org_ids_with_dataframe(
        #     access_token=access_token,
        #     dataframe_id=to_boolean_in.dataframe_id,
        # )

        analysis = (
            db.query(Analysis).filter(Analysis.id == to_boolean_in.analysis_id).first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )

        logger.info(
            "[V6] Running to_boolean for session_id=%s on dataframes=%s",
            analysis.session_id_vantage,
            dataframe_ids,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column": to_boolean_in.column,
            "output_column": to_boolean_in.output_column,
            "true_values": to_boolean_in.true_values,
        }

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:

                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    logger.info("[V6] Organization IDs fetched: %s", org_ids)
                    payload = {
                        "dataframe_id": df_id,
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
                        "[V6] Payload to send to Vantage6 for to_boolean:\n%s",
                        json.dumps(payload, indent=2),
                    )

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )

                    response.raise_for_status()

                    response_data = response.json()

                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]
                    self.update_cohort_task_id(
                        db=db, dataframe_id=df_id, task_id=task_id
                    )

                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))

            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )
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

    def create_one_hot_encoding(
        self,
        db: Session,
        *,
        access_token: str,
        one_hot_encoding_in: OneHotEncodingRequest,
    ) -> V6TaskResult:
        """
        Executes a one_hot_encode preprocessing task in Vantage6.
        Creates a binary column for each category in the specified column.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "one_hot_encode"

        logger.info(
            "[V6] create_one_hot_encoding START for analysis_id=%s",
            one_hot_encoding_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        # org_ids = self._get_org_ids_with_dataframe(
        #     access_token=access_token,
        #     dataframe_id=one_hot_encoding_in.dataframe_id,
        # )

        # logger.info("[V6] Organization IDs fetched: %s", org_ids)

        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == one_hot_encoding_in.analysis_id)
            .first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column": one_hot_encoding_in.column,
            "prefix": one_hot_encoding_in.prefix,
        }

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:

                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    payload = {
                        "dataframe_id": df_id,
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
                        "[V6] Payload to send to Vantage6 for one_hot_encode:\n%s",
                        json.dumps(payload, indent=2),
                    )

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )

                    response.raise_for_status()

                    response_data = response.json()

                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]

                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))

                    self.update_cohort_task_id(
                        db=db,
                        dataframe_id=df_id,
                        task_id=task_id,
                    )
            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )

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

    def create_merge_variables(
        self,
        db: Session,
        *,
        access_token: str,
        merge_variables_in: MergeVariablesRequest,
    ) -> V6TaskResult:
        """
        Executes a merge_variables preprocessing task in Vantage6.
        Concatenates two columns into a new output column.
        """
        IMAGE = "ghcr.io/iknl/preprocessing:latest"
        METHOD = "merge_variables"

        logger.info(
            "[V6] create_merge_variables START for analysis_id=%s",
            merge_variables_in.analysis_id,
        )

        if not self.base_url:
            logger.warning("External data_preparation URL not configured")
            return

        # org_ids = self._get_org_ids_with_dataframe(
        #     access_token=access_token,
        #     dataframe_id=merge_variables_in.dataframe_id,
        # )

        analysis = (
            db.query(Analysis)
            .filter(Analysis.id == merge_variables_in.analysis_id)
            .first()
        )

        dataframe_ids = self._get_session_dataframe_ids(
            access_token=access_token,
            session_id=analysis.session_id_vantage,
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        arguments = {
            "column1": merge_variables_in.column1,
            "column2": merge_variables_in.column2,
            "output_column": merge_variables_in.output_column,
        }

        results = []

        try:
            with httpx.Client(timeout=self.timeout) as client:

                for df_id in dataframe_ids:

                    org_ids = self._get_org_ids_with_dataframe(
                        access_token=access_token,
                        dataframe_id=df_id,
                    )

                    logger.info("[V6] Organization IDs fetched: %s", org_ids)

                    payload = {
                        "dataframe_id": df_id,
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
                        "[V6] Payload to send to Vantage6 for merge_variables:\n%s",
                        json.dumps(payload, indent=2),
                    )

                    response = self._post_preprocess_with_retry(
                        client=client,
                        dataframe_id=df_id,
                        payload=payload,
                        headers=headers,
                    )
                    response.raise_for_status()

                    response_data = response.json()

                    logger.debug(
                        "[V6] Full response data: %s",
                        json.dumps(response_data, indent=2),
                    )

                    task_id = response_data["last_session_task"]["id"]
                    job_id = response_data["last_session_task"]["job_id"]

                    results.append(V6TaskResult(task_id=task_id, job_id=job_id))

                    self.update_cohort_task_id(
                        db=db, dataframe_id=df_id, task_id=task_id
                    )
            self.delete_summary_after_session(
                db=db, session_id=analysis.session_id_vantage
            )

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

    def update_cohort_task_id(
        self, db: Session, *, dataframe_id: int, task_id: int
    ) -> bool:
        """
        Updates the task_id_vantage for the cohort that owns the given dataframe_id.
        """
        cohort = (
            db.query(Cohort).filter(Cohort.dataframe_vantage_id == dataframe_id).first()
        )

        if not cohort:
            logger.warning(
                "[V6] No cohort found for dataframe_id=%s to update task_id",
                dataframe_id,
            )
            return False

        cohort.task_id_vantage = task_id
        db.add(cohort)
        db.commit()
        logger.info(
            "[V6] Updated cohort_id=%s task_id_vantage=%s for dataframe_id=%s",
            cohort.id,
            task_id,
            dataframe_id,
        )
        return True

    def delete_summary_after_update_variables(
        self, db: Session, *, dataframe_id: int
    ) -> bool:

        cohorts = (
            db.query(Cohort).filter(Cohort.dataframe_vantage_id == dataframe_id).all()
        )

        if not cohorts:
            logger.info("[V6] No cohorts found for dataframe_id=%s", dataframe_id)
            return True

        for cohort in cohorts:
            # Find all algorithms with method_name == "summary" linked to this cohort
            summary_algorithms = (
                db.query(Algorithm)
                .join(CohortAlgorithm, CohortAlgorithm.algorithm_id == Algorithm.id)
                .filter(
                    CohortAlgorithm.cohort_id == cohort.id,
                    Algorithm.method_name.in_(["summary", "table1"]),
                )
                .all()
            )

            if summary_algorithms:
                logger.info(
                    "[V6] Found %d summary algorithms for cohort_id=%s",
                    len(summary_algorithms),
                    cohort.id,
                )

                # Delete the CohortAlgorithm associations first
                for algorithm in summary_algorithms:
                    cohort_alg = (
                        db.query(CohortAlgorithm)
                        .filter(
                            CohortAlgorithm.cohort_id.in_([cohort.id]),
                            CohortAlgorithm.algorithm_id == algorithm.id,
                        )
                        .first()
                    )
                    if cohort_alg:
                        db.delete(cohort_alg)
                        logger.info(
                            "[V6] Deleted CohortAlgorithm link for algorithm_id=%s",
                            algorithm.id,
                        )

                # Delete the Algorithm records
                for algorithm in summary_algorithms:
                    db.delete(algorithm)
                    logger.info(
                        "[V6] Deleted algorithm_id=%s (method_name=summary)",
                        algorithm.id,
                    )

        db.commit()
        logger.info(
            "[V6] Successfully deleted summary algorithms for dataframe_id=%s",
            dataframe_id,
        )
        return True

    @staticmethod
    def map_coe_codes_to_org_ids(coe_codes: List[str]) -> List[int]:
        org_ids = []
        unknown = []

        for code in coe_codes:
            if code in COE_CODE_ORG_ID_MAP:
                org_ids.append(COE_CODE_ORG_ID_MAP[code])
            else:
                unknown.append(code)

        if unknown:
            raise ValueError(f"Unknown COE codes: {unknown}")

        return org_ids

    def _get_org_ids_create_cohort(
        self,
        *,
        access_token: str,
        db: Session,
        workspace_id: int,
    ) -> list[int]:

        org_ids = list(
            self._get_online_organization_ids(
                access_token=access_token,
                collaboration_id=COLLABORATION_ID,
            )
        )

        logger.info(
            "[V6] Initial org IDs for collaboration_id=%s: %s",
            COLLABORATION_ID,
            org_ids,
        )

        authorized_org_ids = None

        authorized_org_ids = self._get_authorized_org_ids(
            db=db,
            workspace_id=workspace_id,
        )

        if authorized_org_ids is not None:
            org_ids = [oid for oid in org_ids if oid in authorized_org_ids]

        logger.info(
            "[V6] Org IDs after applying permit filter for workspace_id=%s: %s",
            workspace_id,
            org_ids,
        )
        return org_ids

    def _get_org_ids_with_dataframe(
        self,
        *,
        access_token: str,
        dataframe_id: int,
    ) -> list[int]:

        org_ids = list(
            self._get_online_organization_ids(
                access_token=access_token,
                collaboration_id=COLLABORATION_ID,
            )
        )

        logger.info(
            "[V6] Initial _get_org_ids_with_dataframe IDs for collaboration_id=%s: %s",
            COLLABORATION_ID,
            org_ids,
        )

        df_org_ids = self._get_orgs_with_dataframe(
            access_token=access_token,
            dataframe_id=dataframe_id,
        )

        logger.info(
            "[V6]  _get_org_ids_with_dataframe results from dataframe: %s",
            df_org_ids,
        )

        if df_org_ids:
            org_ids = [oid for oid in org_ids if oid in df_org_ids]

        logger.info(
            "[V6] Final _get_org_ids_with_dataframe IDs for collaboration_id=%s: %s",
            COLLABORATION_ID,
            org_ids,
        )

        return org_ids

    def _get_authorized_org_ids(
        self,
        *,
        db: Session,
        workspace_id: int,
    ) -> set[int]:

        permit = (
            db.query(Permit)
            .filter(
                Permit.workspace_id == workspace_id,
                Permit.status == PermitStatus.GRANTED,
            )
            .first()
        )
        if not permit or not permit.coes_granted:
            logger.info(
                "[V6] No granted permit found for workspace %s",
                workspace_id,
            )
            return set()

        org_ids = []
        unknown_codes = []
        for code in permit.coes_granted:
            if code in COE_CODE_ORG_ID_MAP:
                org_ids.append(COE_CODE_ORG_ID_MAP[code])
            else:
                unknown_codes.append(code)

        if unknown_codes:
            logger.warning(
                "[V6] Unknown COE codes in granted permit for workspace %s: %s",
                workspace_id,
                unknown_codes,
            )

        return set(org_ids)

    def _get_session_dataframe_ids(
        self, access_token: str, session_id: int
    ) -> List[int]:
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(
                f"{self.base_url}/session/{session_id}/dataframe?per_page=999",
                headers=headers,
            )
        response.raise_for_status()

        data = response.json()["data"]

        return [df["id"] for df in data]

    # def delete_summary_after_session(
    #     self,
    #     db: Session,
    #     *,
    #     session_id: int,
    # ) -> bool:
    #     """
    #     Deletes all summary algorithms linked to cohorts that belong to the given session_id.
    #     Should be called after a session is completed to clean up old summary results.
    #     """
    #     cohorts = (
    #         db.query(Cohort)
    #         .join(Analysis)
    #         .filter(Analysis.session_id_vantage == session_id)
    #         .all()
    #     )

    #     if not cohorts:
    #         logger.info("[V6] No cohorts found for session_id=%s", session_id)
    #         return True

    #     cohort_ids = [c.id for c in cohorts]
    #     logger.info(
    #         "[V6] Found %d cohorts: %s for session_id=%s",
    #         len(cohorts),
    #         cohort_ids,
    #         session_id,
    #     )

    #     algorithm_rows = (
    #         db.query(Algorithm.id)
    #         .join(CohortAlgorithm, CohortAlgorithm.algorithm_id == Algorithm.id)
    #         .filter(
    #             CohortAlgorithm.cohort_id.in_(cohort_ids),
    #             Algorithm.method_name.in_(["summary", "table1"]),
    #         )
    #         .distinct()
    #         .all()
    #     )

    #     algorithm_ids = [row[0] for row in algorithm_rows]
    #     logger.info(
    #         "[V6] Found %d algorithms to delete: %s",
    #         len(algorithm_ids),
    #         algorithm_ids,
    #     )

    #     for cohort in cohorts:
    #         # Find all algorithms with method_name == "summary" linked to this cohort
    #         summary_algorithms = (
    #             db.query(Algorithm)
    #             .join(CohortAlgorithm, CohortAlgorithm.algorithm_id == Algorithm.id)
    #             .filter(
    #                 CohortAlgorithm.cohort_id == cohort.id,
    #                 Algorithm.method_name.in_(["summary", "table1"]),
    #             )
    #             .distinct()
    #             .all()
    #         )

    #         if summary_algorithms:
    #             logger.info(
    #                 "[V6] Found %d summary algorithms for cohort_id=%s",
    #                 len(summary_algorithms),
    #                 cohort.id,
    #             )

    #             # Delete the CohortAlgorithm associations first
    #             for algorithm in summary_algorithms:
    #                 cohort_alg = (
    #                     db.query(CohortAlgorithm)
    #                     .filter(
    #                         CohortAlgorithm.algorithm_id == algorithm.id,
    #                     )
    #                     .distinct()
    #                     .all()
    #                 )
    #                 if cohort_alg:
    #                     db.delete(cohort_alg)
    #                     logger.info(
    #                         "[V6] Deleted CohortAlgorithm link for algorithm_id=%s",
    #                         algorithm.id,
    #                     )

    #             # Delete the Algorithm records
    #             for algorithm in summary_algorithms:
    #                 db.delete(algorithm)
    #                 logger.info(
    #                     "[V6] Deleted algorithm_id=%s (method_name=summary)",
    #                     algorithm.id,
    #                 )

    #     db.commit()
    #     logger.info(
    #         "[V6] Successfully deleted summary algorithms for session_id=%s",
    #         session_id,
    #     )
    #     return True

    def delete_summary_after_session(
        self,
        db: Session,
        *,
        session_id: int,
    ) -> bool:

        cohorts = (
            db.query(Cohort)
            .join(Analysis)
            .filter(Analysis.session_id_vantage == session_id)
            .all()
        )

        if not cohorts:
            logger.info("[V6] No cohorts found for session_id=%s", session_id)
            return True

        cohort_ids = [c.id for c in cohorts]

        algorithm_ids = [
            row[0]
            for row in (
                db.query(Algorithm.id)
                .join(CohortAlgorithm, CohortAlgorithm.algorithm_id == Algorithm.id)
                .filter(
                    CohortAlgorithm.cohort_id.in_(cohort_ids),
                    Algorithm.method_name.in_(["summary", "table1"]),
                )
                .distinct()
                .all()
            )
        ]

        if not algorithm_ids:
            logger.info("[V6] No summary/table1 algorithms to delete")
            return True

        # 🔥 1. Delete associations (bulk)
        db.query(CohortAlgorithm).filter(
            CohortAlgorithm.cohort_id.in_(cohort_ids),
            CohortAlgorithm.algorithm_id.in_(algorithm_ids),
        ).delete(synchronize_session=False)

        # 🔥 2. Delete algorithms (bulk)
        db.query(Algorithm).filter(Algorithm.id.in_(algorithm_ids)).delete(
            synchronize_session=False
        )

        db.commit()

        logger.info(
            "[V6] Deleted %d algorithms and their associations for session_id=%s",
            len(algorithm_ids),
            session_id,
        )

        return True


vantage6_service = Vantage6Service()
