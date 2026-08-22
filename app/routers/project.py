from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.db.schema.user import UserOutput
from app.util.protectRoute import get_current_user, get_current_admin
from app.service.projectService import ProjectService

projectRouter = APIRouter()

# Schema representation for project metadata return
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ProjectOutput(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    file_name: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

@projectRouter.post("", response_model=ProjectOutput, status_code=201)
def create_project(
    name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
    current_user: UserOutput = Depends(get_current_user)
):
    try:
        return ProjectService(session=session).create_project(
            name=name,
            description=description,
            file=file,
            owner_id=current_user.id
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@projectRouter.get("", response_model=List[ProjectOutput])
def get_user_projects(
    session: Session = Depends(get_db),
    current_user: UserOutput = Depends(get_current_user)
):
    try:
        return ProjectService(session=session).get_projects_by_owner(owner_id=current_user.id)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@projectRouter.get("/all", response_model=List[ProjectOutput])
def get_all_projects(
    session: Session = Depends(get_db),
    admin_user: UserOutput = Depends(get_current_admin)
):
    try:
        return ProjectService(session=session).get_all_projects()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@projectRouter.get("/{project_id}/data")
def get_project_data(
    project_id: int,
    session: Session = Depends(get_db),
    current_user: UserOutput = Depends(get_current_user)
):
    try:
        is_admin = (current_user.role == "Admin")
        return ProjectService(session=session).parse_project_data(
            project_id=project_id,
            current_user_id=current_user.id,
            is_admin=is_admin
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@projectRouter.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_db),
    current_user: UserOutput = Depends(get_current_user)
):
    try:
        is_admin = (current_user.role == "Admin")
        return ProjectService(session=session).delete_project(
            project_id=project_id,
            current_user_id=current_user.id,
            is_admin=is_admin
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

@projectRouter.post("/{project_id}/chat")
async def chat_with_project(
    project_id: int,
    request: ChatRequest,
    session: Session = Depends(get_db),
    current_user: UserOutput = Depends(get_current_user)
):
    from app.service.chat_service import ChatService
    from app.db.repository.projectRepo import ProjectRepository
    try:
        is_admin = (current_user.role == "Admin")
        project = ProjectRepository(session=session).get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        if project.owner_id != current_user.id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this project")
            
        chat_service = ChatService(db=session, project_id=project_id, file_path=project.file_path)
        answer = chat_service.ask_question(request.message)
        return {"answer": answer}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
