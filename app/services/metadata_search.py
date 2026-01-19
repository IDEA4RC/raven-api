"""
Service for handling permit operations
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.permit import Permit
from app.models.workspace import Workspace
from app.models.workspace_history import WorkspaceHistory
from app.schemas.metadata_search import MetadataSearch
from app.services.base import BaseService
from app.utils.constants import PermitStatus, DataAccessStatus


class MetadataSearchService(BaseService[MetadataSearch]):
    """
    Service for handling metadata search operations
    """

    model = MetadataSearch

    def get_permit_metadata_search(
        self,
        db: Session,
        permit_number: str,
        workspace_id: Optional[int] = None
    ) -> List[MetadataSearch]:
        """
        Get metadata search records for a given permit number and optional workspace ID.

        :param db: Database session
        :param permit_number: Permit number to filter by
        :param workspace_id: Optional workspace ID to filter by
        :return: List of MetadataSearch records
        """
        query = db.query(MetadataSearch).join(Permit).filter(
            Permit.permit_number == permit_number
        )

        if workspace_id is not None:
            query = query.filter(MetadataSearch.workspace_id == workspace_id)

        return query.all()