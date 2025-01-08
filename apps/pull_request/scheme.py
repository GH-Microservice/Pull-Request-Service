from pydantic import BaseModel
from utils.scheme import SUser
from typing import Optional
from datetime import datetime
from enum import Enum



class CreatePullRequestScheme(BaseModel):
    repository_id: int
    letter: Optional[str]


class CreatePullReqForOrganization(BaseModel):
    organization_id: int
    letter: Optional[str]



class PullRequestSchema(BaseModel):
    id: int
    letter: Optional[str] = None
    status: str
    user: Optional[SUser] = None
    created_at: datetime



class RepositorySchema(BaseModel):
    id: int
    repository_title: str
    user: SUser



class UpdatePullRequestScheme(BaseModel):
    id: int
    letter: Optional[str] = None
    status: str