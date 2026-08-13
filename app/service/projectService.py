import os
import shutil
import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.db.repository.projectRepo import ProjectRepository
from app.db.models.project import Project

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")

class ProjectService:
    def __init__(self, session: Session):
        self.__projectRepository = ProjectRepository(session=session)

    def create_project(self, name: str, description: str, file: UploadFile, owner_id: int) -> Project:
        # Validate file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".csv", ".xlsx"]:
            raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

        # Ensure upload directory exists
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Save file to upload directory
        # Generate unique filename to prevent collisions
        import uuid
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        return self.__projectRepository.create_project(
            name=name,
            description=description,
            file_name=file.filename,
            file_path=file_path,
            owner_id=owner_id
        )

    def get_projects_by_owner(self, owner_id: int):
        return self.__projectRepository.get_projects_by_owner(owner_id)

    def get_all_projects(self):
        return self.__projectRepository.get_all_projects()

    def get_project_by_id(self, project_id: int) -> Project:
        project = self.__projectRepository.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    def delete_project(self, project_id: int, current_user_id: int, is_admin: bool):
        project = self.get_project_by_id(project_id)
        
        # Enforce ownership/admin permission
        if project.owner_id != current_user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to delete this project")

        # Delete physical file from disk
        if os.path.exists(project.file_path):
            try:
                os.remove(project.file_path)
            except Exception as e:
                # Log the error but proceed to delete database entry
                print(f"Error removing file {project.file_path}: {e}")

        # Delete database entry
        self.__projectRepository.delete_project(project_id)
        return {"message": "Project and its file deleted successfully"}

    def parse_project_data(self, project_id: int, current_user_id: int, is_admin: bool):
        project = self.get_project_by_id(project_id)

        # Enforce permission
        if project.owner_id != current_user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to access this project's data")

        if not os.path.exists(project.file_path):
            raise HTTPException(status_code=404, detail="Project data file missing on server")

        ext = os.path.splitext(project.file_path)[1].lower()

        try:
            if ext == ".csv":
                df = pd.read_csv(project.file_path)
            elif ext == ".xlsx":
                df = pd.read_excel(project.file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")

            # Clean/Replace NaN/NaT values so they serialize as proper JSON null
            df = df.astype(object).where(pd.notnull(df), None)

            # Limit rows to prevent massive payloads if files are giant (e.g. max 5000 rows for view)
            # Standard excel sheets for this kind of demo usually fit fine.
            # Let's keep it full unless it's extremely huge, say limit to 10000 rows.
            if len(df) > 10000:
                df = df.head(10000)

            # Clean columns: rename duplicate columns or empty ones
            df.columns = [str(col).strip() if pd.notnull(col) else f"Unnamed_{i}" for i, col in enumerate(df.columns)]

            headers = list(df.columns)
            rows = df.to_dict(orient="records")

            return {
                "headers": headers,
                "rows": rows
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")
