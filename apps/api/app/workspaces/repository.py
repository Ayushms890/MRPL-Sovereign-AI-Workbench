from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.domain.entities import Workspace, WorkspaceMember, User
from app.infrastructure.models import WorkspaceModel, WorkspaceMemberModel, UserModel, utc_now


class WorkspaceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, name: str, owner_id: str) -> Workspace:
        ws_id = f"ws_{uuid4().hex[:16]}"
        workspace = WorkspaceModel(
            id=ws_id,
            name=name,
            owner_id=owner_id,
            created_at=utc_now(),
        )
        self.session.add(workspace)
        self.session.flush()

        # Add owner member
        mem_id = f"wm_{uuid4().hex[:16]}"
        member = WorkspaceMemberModel(
            id=mem_id,
            workspace_id=ws_id,
            user_id=owner_id,
            role="owner",
            joined_at=utc_now(),
        )
        self.session.add(member)
        self.session.commit()
        self.session.refresh(workspace)
        return self._workspace_to_entity(workspace)

    def get_by_id(self, workspace_id: str) -> Workspace | None:
        ws = self.session.get(WorkspaceModel, workspace_id)
        return self._workspace_to_entity(ws) if ws else None

    def get_for_user(self, user_id: str) -> list[Workspace]:
        stmt = (
            select(WorkspaceModel)
            .join(WorkspaceMemberModel, WorkspaceModel.id == WorkspaceMemberModel.workspace_id)
            .where(WorkspaceMemberModel.user_id == user_id)
            .order_by(WorkspaceModel.created_at.desc())
        )
        workspaces = self.session.scalars(stmt).all()
        return [self._workspace_to_entity(ws) for ws in workspaces]

    def get_personal_workspace(self, user_id: str) -> Workspace | None:
        stmt = (
            select(WorkspaceModel)
            .where(
                and_(
                    WorkspaceModel.owner_id == user_id,
                    WorkspaceModel.name == "Personal",
                )
            )
            .order_by(WorkspaceModel.created_at.asc())
        )
        ws = self.session.scalars(stmt).first()
        if not ws:
            workspaces = self.get_for_user(user_id)
            return workspaces[0] if workspaces else None
        return self._workspace_to_entity(ws)

    def get_member_role(self, workspace_id: str, user_id: str) -> str | None:
        stmt = select(WorkspaceMemberModel.role).where(
            and_(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        return self.session.scalar(stmt)

    def add_member(self, workspace_id: str, user_id: str, role: str) -> WorkspaceMember:
        mem_id = f"wm_{uuid4().hex[:16]}"
        member = WorkspaceMemberModel(
            id=mem_id,
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            joined_at=utc_now(),
        )
        self.session.add(member)
        self.session.commit()
        self.session.refresh(member)
        return self._member_to_entity(member)

    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        stmt = select(WorkspaceMemberModel).where(
            and_(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        member = self.session.scalar(stmt)
        if not member:
            return False
        self.session.delete(member)
        self.session.commit()
        return True

    def update_member_role(self, workspace_id: str, user_id: str, role: str) -> WorkspaceMember | None:
        stmt = select(WorkspaceMemberModel).where(
            and_(
                WorkspaceMemberModel.workspace_id == workspace_id,
                WorkspaceMemberModel.user_id == user_id,
            )
        )
        member = self.session.scalar(stmt)
        if not member:
            return None
        member.role = role
        self.session.commit()
        self.session.refresh(member)
        return self._member_to_entity(member)

    def list_members(self, workspace_id: str) -> list[tuple[WorkspaceMember, User]]:
        stmt = (
            select(WorkspaceMemberModel, UserModel)
            .join(UserModel, WorkspaceMemberModel.user_id == UserModel.id)
            .where(WorkspaceMemberModel.workspace_id == workspace_id)
            .order_by(WorkspaceMemberModel.joined_at.asc())
        )
        rows = self.session.execute(stmt).all()
        result = []
        for mem_model, user_model in rows:
            user_entity = User(
                id=user_model.id,
                email=user_model.email,
                name=user_model.name,
                emailVerified=user_model.emailVerified,
                createdAt=user_model.createdAt,
                updatedAt=user_model.updatedAt,
                image=user_model.image,
                preferred_provider=user_model.preferred_provider,
            )
            result.append((self._member_to_entity(mem_model), user_entity))
        return result

    @staticmethod
    def _workspace_to_entity(ws: WorkspaceModel) -> Workspace:
        return Workspace(
            id=ws.id,
            name=ws.name,
            owner_id=ws.owner_id,
            created_at=ws.created_at,
        )

    @staticmethod
    def _member_to_entity(mem: WorkspaceMemberModel) -> WorkspaceMember:
        return WorkspaceMember(
            id=mem.id,
            workspace_id=mem.workspace_id,
            user_id=mem.user_id,
            role=mem.role,
            joined_at=mem.joined_at,
        )
