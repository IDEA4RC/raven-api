"""
Service for handling permit operations
"""

from sqlalchemy.orm import Session

from app.models.metadata_search import MetadataSearch
from app.schemas.metadata_search import (
    MetadataSearchBase,
    MetadataSearchCreate,
    MetadataSearchUpdate,
)
from app.services.base import BaseService


class MetadataSearchService(BaseService[MetadataSearch, None, None]):
    """
    Service for handling metadata search operations
    """

    def get_metadata_search_by_workspace(
        self, db: Session, *, workspace_id: int
    ) -> MetadataSearch:
        """
        Get metadata search records for a given  workspace ID.

        :param db: Database session
        :param workspace_id: workspace ID to filter by
        :return: MetadataSearch records
        """
        metadata_search = (
            db.query(MetadataSearch)
            .filter(MetadataSearch.workspace_id == workspace_id)
            .one()
        )

        return metadata_search


metadata_search_service = MetadataSearchService(MetadataSearch)
