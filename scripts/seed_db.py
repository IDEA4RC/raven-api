"""
Script to seed the database with example data
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.models import Organization, User, UserType, Team, UserTeam, Workspace, Permit, WorkspaceHistory
from app.utils.constants import PermitStatus, DataAccessStatus

def seed_database():
    """
    Insert example data into the database
    """
    print("Seeding database with example data...")
    db = SessionLocal()
    
    try:
        # Create organizations
        print("Creating organizations...")
        org1 = Organization(
            org_name="University Hospital",
            description="A major teaching hospital and research center",
            org_city="Madrid",
            org_type=1  # Academic
        )
        org2 = Organization(
            org_name="Medical Research Center",
            description="Independent medical research institution",
            org_city="Barcelona",
            org_type=2  # Industry
        )
        
        db.add_all([org1, org2])
        db.commit()
        
        # Create user types
        print("Creating user types...")
        admin_type = UserType(
            description="Administrator",
            metadata_search=4,  # create
            permissions=1,      # yes
            cohort_builder=1,   # yes
            data_quality=2,     # view/export
            export=4,           # export
            results_report=3    # edit/export
        )
        researcher_type = UserType(
            description="Researcher",
            metadata_search=3,  # edit
            permissions=1,      # yes
            cohort_builder=1,   # yes
            data_quality=1,     # view
            export=2,           # view
            results_report=2    # view
        )
        
        db.add_all([admin_type, researcher_type])
        db.commit()
        
        # Create users
        print("Creating users...")
        user1 = User(
            username="admin",
            email="admin@example.com",
            organization_id=org1.id,
            user_type_id=admin_type.id,
            keycloak_id="keycloak-id-1",
            first_name="Admin",
            last_name="User",
            is_active=True
        )
        user2 = User(
            username="researcher",
            email="researcher@example.com",
            organization_id=org1.id,
            user_type_id=researcher_type.id,
            keycloak_id="keycloak-id-2",
            first_name="Research",
            last_name="Scientist",
            is_active=True
        )
        user3 = User(
            username="scientist",
            email="scientist@example.com",
            organization_id=org2.id,
            user_type_id=researcher_type.id,
            keycloak_id="keycloak-id-3",
            first_name="Medical",
            last_name="Scientist",
            is_active=True
        )
        
        db.add_all([user1, user2, user3])
        db.commit()
        
        # Create teams
        print("Creating teams...")
        team1 = Team(
            team_name="Cancer Research Team",
            team_contact_name="Dr. Smith",
            address="Hospital Avenue 123, Madrid"
        )
        team2 = Team(
            team_name="Genomics Team",
            team_contact_name="Dr. Johnson",
            address="Science Park 456, Barcelona"
        )
        
        db.add_all([team1, team2])
        db.commit()
        
        # Create user-team associations
        print("Creating user-team associations...")
        user_team1 = UserTeam(user_id=user1.id, team_id=team1.id)
        user_team2 = UserTeam(user_id=user2.id, team_id=team1.id)
        user_team3 = UserTeam(user_id=user3.id, team_id=team2.id)
        
        db.add_all([user_team1, user_team2, user_team3])
        db.commit()
        
        # Create permits
        print("Creating permits...")
        permit1 = Permit(
            permit_name="Cancer Data Access",
            creation_date=datetime.utcnow(),
            validity_date=datetime(2025, 12, 31),
            team_id=team1.id,
            status=4  # granted
        )
        permit2 = Permit(
            permit_name="Genomics Data Access",
            creation_date=datetime.utcnow(),
            validity_date=datetime(2026, 6, 30),
            team_id=team2.id,
            status=2  # submitted
        )
        
        db.add_all([permit1, permit2])
        db.commit()
        
        # Create workspaces
        print("Creating workspaces...")
        workspace1 = Workspace(
            name="Cancer Research Workspace",
            description="Workspace for cancer research projects",
            team_id=team1.id,
            creator_id=user1.id,
            data_access=DataAccessStatus.APPROVED,      # granted
            last_edit=datetime.utcnow()
        )
        workspace2 = Workspace(
            name="Genomics Analysis Workspace",
            description="Workspace for genomic data analysis",
            team_id=team2.id,
            creator_id=user2.id,
            data_access=DataAccessStatus.SUBMITTED,      # submitted
            last_edit=datetime.utcnow()
        )
        
        db.add_all([workspace1, workspace2])
        db.commit()
        
        # Create permits for workspaces
        print("Creating permits...")
        permit1 = Permit(
            status=PermitStatus.APPROVED,  # approved
            update_date=datetime.utcnow(),
            workspace_id=workspace1.id
        )
        permit2 = Permit(
            status=PermitStatus.SUBMITTED,  # submitted
            update_date=datetime.utcnow(),
            workspace_id=workspace2.id
        )
        
        db.add_all([permit1, permit2])
        db.commit()
        
        # Create workspace history
        print("Creating workspace history...")
        history1 = WorkspaceHistory(
            date=datetime.utcnow(),
            action="Workspace created",
            phase="Creation",
            details="Initial workspace setup",
            creator_id=user1.id,
            workspace_id=workspace1.id
        )
        
        history2 = WorkspaceHistory(
            date=datetime.utcnow(),
            action="Data access application submitted",
            phase="Data Permit",
            details="The data permit application has been submitted",
            creator_id=user1.id,
            workspace_id=workspace1.id
        )
        
        history3 = WorkspaceHistory(
            date=datetime.utcnow(),
            action="Data access application approved",
            phase="Data Permit",
            details="The data permit application has been approved",
            creator_id=user1.id,
            workspace_id=workspace1.id
        )
        
        history4 = WorkspaceHistory(
            date=datetime.utcnow(),
            action="Workspace created",
            phase="Creation",
            details="Initial workspace setup",
            creator_id=user3.id,
            workspace_id=workspace2.id
        )
        
        history5 = WorkspaceHistory(
            date=datetime.utcnow(),
            action="Data access application submitted",
            phase="Data Permit",
            details="The data permit application has been submitted",
            creator_id=user3.id,
            workspace_id=workspace2.id
        )
        
        db.add_all([history1, history2, history3, history4, history5])
        db.commit()
        
        print("Database seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
