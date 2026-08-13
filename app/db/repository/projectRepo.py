from .base import BaseRepository
from app.db.models.project import Project

class ProjectRepository(BaseRepository):
    def create_project(self, name: str, description: str, file_name: str, file_path: str, owner_id: int) -> Project:
        new_project = Project(
            name=name,
            description=description,
            file_name=file_name,
            file_path=file_path,
            owner_id=owner_id
        )
        self.session.add(instance=new_project)
        self.session.commit()
        self.session.refresh(instance=new_project)
        return new_project

    def get_projects_by_owner(self, owner_id: int):
        return self.session.query(Project).filter_by(owner_id=owner_id).all()

    def get_all_projects(self):
        return self.session.query(Project).all()

    def get_project_by_id(self, project_id: int) -> Project:
        return self.session.query(Project).filter_by(id=project_id).first()

    def delete_project(self, project_id: int) -> bool:
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        self.session.delete(project)
        self.session.commit()
        return True
