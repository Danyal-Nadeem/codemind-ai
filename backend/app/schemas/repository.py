from pydantic import BaseModel
from datetime import datetime
from app.models.repository import RepoStatus


class RepoCreate(BaseModel):
    github_url: str


class RepoResponse(BaseModel):
    id: str
    github_url: str
    name: str
    status: RepoStatus
    created_at: datetime

    class Config:
        from_attributes = True
