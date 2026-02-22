from http.client import HTTPException

from sqlalchemy.orm import Session

from app.services.vantage_6 import vantage6_service
from app.services.workspace import workspace_service

from app.schemas.workspace import WorkspaceCreateV2
from app.models.workspace import Workspace
import logging

logger = logging.getLogger(__name__)
from app.schemas.workspace import Workspace


class AnalysisOrchestratorService:

    def create_workspace_full(
        self,
        *,
        db: Session,
        workspace_in: WorkspaceCreateV2,
        user_id: int,
        access_token: str,
    ) -> dict:
        logger.info("[API] Calling Vantage6Service.register_workspace")

        try:
            v6_study_id = vantage6_service.register_workspace(
                workspace_name=workspace_in.name,
                access_token=access_token,
            )

        except RuntimeError as e:
            logger.error("[API] Vantage6Service failed: %s", str(e))
            raise HTTPException(
                status_code=500, detail=f"Cannot create workspace in Vantage6: {str(e)}"
            )

        workspace_in.v6_study_id = v6_study_id
        logger.info("[API] Calling workspace_service.create_with_history_v2")

        workspace = workspace_service.create_with_history_v2(
            db=db, obj_in=workspace_in, user_id=user_id
        )

        if not workspace:
            logger.error("[API] Failed to create workspace in local DB")
            raise HTTPException(
                status_code=500, detail="Workspace could not be created in local DB"
            )

        logger.info(
            "[API] Workspace created successfully with v6_study_id=%s", v6_study_id
        )

        return workspace


workspace_orchestrator_service = AnalysisOrchestratorService()
