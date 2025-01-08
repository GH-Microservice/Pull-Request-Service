from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import StrictRedis
from aio_pika import RobustConnection
from apps.pull_request.scheme import (
    CreatePullReqForOrganization,
    CreatePullRequestScheme,
    PullRequestSchema,
    UpdatePullRequestScheme
)
from apps.pull_request.service import PullRequestService
from utils.scheme import SUser
from utils.utils import get_current_user, get_redis_cli, get_rmq_connection
from database.pull_request_database import get_pull_request_sesison


pull_request_service_router = APIRouter(
    tags=["Pull Request Service"], prefix="/pull-request/api/v1"
)


@pull_request_service_router.post(
    "/create-pull-request-repository/", response_model=CreatePullRequestScheme
)
async def create_pull_request_repository(
    request: CreatePullRequestScheme,
    session: AsyncSession = Depends(get_pull_request_sesison),
    current_user: SUser = Depends(get_current_user),
):
    service = PullRequestService(session=session, current_user=current_user)
    return await service._create_pull_request_repository(request=request)


@pull_request_service_router.post(
    "/create-pull-request-organization/", response_model=CreatePullReqForOrganization
)
async def create_pull_request_repository(
    request: CreatePullReqForOrganization,
    session: AsyncSession = Depends(get_pull_request_sesison),
    current_user: SUser = Depends(get_current_user),
):
    service = PullRequestService(session=session, current_user=current_user)
    return await service._create_pull_request_organization(request=request)


@pull_request_service_router.get(
    "/get-pull-requests-repository/{repository_id}/",
    response_model=list[PullRequestSchema],
)
async def get_pull_requests_repository(
    repository_id: int,
    session: AsyncSession = Depends(get_pull_request_sesison),
    rmq_cli: RobustConnection = Depends(get_rmq_connection),
    redis_cli: StrictRedis = Depends(get_redis_cli),
):
    service = PullRequestService(session=session, rmq_cli=rmq_cli, redis_cli=redis_cli)
    return await service._get_repositorys_pull_request(repository_id=repository_id)


@pull_request_service_router.patch("/update-pull-request/")
async def update_pull_request(
    request: UpdatePullRequestScheme,
    session: AsyncSession = Depends(get_pull_request_sesison),
    current_user: SUser = Depends(get_current_user),
    redis_cli: StrictRedis = Depends(get_redis_cli),
    rmq_cli: RobustConnection = Depends(get_rmq_connection)

):
    
    service = PullRequestService(session=session, current_user=current_user, rmq_cli=rmq_cli, redis_cli = redis_cli)
    return await service._update_pull_request(request=request)