# Contract Repository
# Database persistence for AnalysisContracts
#
# Stores contracts in analysis_contracts table for retrieval by Migration.
#
# Architecture: docs/architecture/workflow-separation-plan.md
# Phase: Fase 21.5 (Week 145-146)

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import logging

from ...contracts import AnalysisContract, AnalysisSourceType

logger = logging.getLogger(__name__)


class ContractRepository:
    """
    Repository for persisting and retrieving AnalysisContracts.

    Usage:
        repo = ContractRepository(db_session)
        repo.save(contract)
        contract = repo.get_by_id(analysis_id)
    """

    def __init__(self, db: Session):
        self.db = db

    def save(self, contract: AnalysisContract) -> str:
        """
        Save an AnalysisContract to the database.

        Args:
            contract: The contract to save

        Returns:
            The analysis_id of the saved contract
        """
        logger.info(f"Saving AnalysisContract {contract.analysis_id}")

        # Use raw SQL for flexibility (table may not have SQLAlchemy model yet)
        query = text("""
            INSERT INTO analysis_contracts (
                analysis_id, source_type, source_id, project_id,
                contract_data, created_at
            ) VALUES (
                :analysis_id, :source_type, :source_id, :project_id,
                :contract_data, :created_at
            )
            ON CONFLICT (analysis_id) DO UPDATE SET
                contract_data = :contract_data,
                updated_at = CURRENT_TIMESTAMP
        """)

        self.db.execute(query, {
            "analysis_id": contract.analysis_id,
            "source_type": contract.source_type.value,
            "source_id": contract.source_id,
            "project_id": contract.project.name,
            "contract_data": json.dumps(contract.to_dict()),
            "created_at": contract.created_at,
        })
        self.db.commit()

        logger.info(f"Saved AnalysisContract {contract.analysis_id}")
        return contract.analysis_id

    def get_by_id(self, analysis_id: str) -> Optional[AnalysisContract]:
        """
        Retrieve an AnalysisContract by its ID.

        Args:
            analysis_id: The contract ID

        Returns:
            The contract if found, None otherwise
        """
        query = text("""
            SELECT contract_data FROM analysis_contracts
            WHERE analysis_id = :analysis_id
        """)

        result = self.db.execute(query, {"analysis_id": analysis_id}).fetchone()

        if not result:
            logger.warning(f"Contract {analysis_id} not found")
            return None

        contract_data = result[0]
        if isinstance(contract_data, str):
            contract_data = json.loads(contract_data)

        return AnalysisContract.from_dict(contract_data)

    def get_by_source_id(
        self,
        source_id: str,
        source_type: Optional[AnalysisSourceType] = None,
    ) -> Optional[AnalysisContract]:
        """
        Retrieve an AnalysisContract by its source ID.

        Args:
            source_id: The original source ID (e.g., brown_paper_session_id)
            source_type: Optional filter by source type

        Returns:
            The contract if found, None otherwise
        """
        if source_type:
            query = text("""
                SELECT contract_data FROM analysis_contracts
                WHERE source_id = :source_id AND source_type = :source_type
                ORDER BY created_at DESC LIMIT 1
            """)
            params = {"source_id": source_id, "source_type": source_type.value}
        else:
            query = text("""
                SELECT contract_data FROM analysis_contracts
                WHERE source_id = :source_id
                ORDER BY created_at DESC LIMIT 1
            """)
            params = {"source_id": source_id}

        result = self.db.execute(query, params).fetchone()

        if not result:
            return None

        contract_data = result[0]
        if isinstance(contract_data, str):
            contract_data = json.loads(contract_data)

        return AnalysisContract.from_dict(contract_data)

    def list_by_project(
        self,
        project_id: str,
        limit: int = 10,
    ) -> List[AnalysisContract]:
        """
        List contracts for a project.

        Args:
            project_id: The project name/ID
            limit: Maximum number of contracts to return

        Returns:
            List of contracts
        """
        query = text("""
            SELECT contract_data FROM analysis_contracts
            WHERE project_id = :project_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        results = self.db.execute(query, {
            "project_id": project_id,
            "limit": limit,
        }).fetchall()

        contracts = []
        for row in results:
            contract_data = row[0]
            if isinstance(contract_data, str):
                contract_data = json.loads(contract_data)
            contracts.append(AnalysisContract.from_dict(contract_data))

        return contracts

    def delete(self, analysis_id: str) -> bool:
        """
        Delete a contract.

        Args:
            analysis_id: The contract ID to delete

        Returns:
            True if deleted, False if not found
        """
        query = text("""
            DELETE FROM analysis_contracts
            WHERE analysis_id = :analysis_id
        """)

        result = self.db.execute(query, {"analysis_id": analysis_id})
        self.db.commit()

        return result.rowcount > 0

    def exists(self, analysis_id: str) -> bool:
        """Check if a contract exists."""
        query = text("""
            SELECT 1 FROM analysis_contracts
            WHERE analysis_id = :analysis_id
        """)

        result = self.db.execute(query, {"analysis_id": analysis_id}).fetchone()
        return result is not None
