from sqlalchemy.orm import Session

from app.services.vantage_6 import vantage6_service
from app.services.workspace import workspace_service

from app.schemas.workspace import WorkspaceCreateV2
from app.models.workspace import Workspace
import logging
logger = logging.getLogger(__name__)
from app.schemas.workspace import Workspace

class AnalysisOrchestratorService():

    def create_workspace_full(
        self,
        *,
        db: Session,
        workspace_in: WorkspaceCreateV2,
        user_id: int,
        access_token: str,
    ) -> Workspace:
    
           
        logger.info("[API] Calling workspace_service.create_with_history_v2")

        workspace = workspace_service.create_with_history_v2(
            db=db, obj_in=workspace_in, user_id=user_id)

          
        if not workspace:
            raise ValueError("Workspace not created properly")
        
        logger.info("[API] Calling Vantage6Service.register_workspace")

        workspaceV6 = vantage6_service.register_workspace(
                        db=db, workspace=workspace,access_token=access_token,
        )

        logger.info("[API] Vantage6Service returned successfully")
        logger.debug("[API] result=%s", workspaceV6)
        return workspaceV6


workspace_orchestrator_service = AnalysisOrchestratorService()