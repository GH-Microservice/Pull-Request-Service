from fastapi import HTTPException
from utils.scheme import SUser
from utils.utils import publish_message, log, consume_data
from sqlalchemy.ext.asyncio import AsyncSession
from config.config import conf
from redis.asyncio import StrictRedis
from apps.pull_request.models import PullRequestModel
from typing import TypeVar, Type, Optional, Any, List
from apps.pull_request.scheme import (
    CreatePullReqForOrganization,
    CreatePullRequestScheme,
    PullRequestSchema,
    RepositorySchema,
    UpdatePullRequestScheme
)
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from fastapi_mail import FastMail, MessageSchema
import aio_pika
import httpx
import json
import asyncio

T = TypeVar("T")


class PullRequestService:
    def __init__(
        self,
        session: AsyncSession,
        current_user: SUser = None,
        redis_cli: StrictRedis = None,
        rmq_cli: aio_pika.RobustConnection = None,
    ):
        self.session = session
        self.current_user = current_user
        self.redis_cli = redis_cli
        self.rmq_cli = rmq_cli

    async def _create_pull_request_repository(self, request: CreatePullRequestScheme):
        return await self._create_object(
            scheme=CreatePullRequestScheme, request=request, model=PullRequestModel
        )

    async def _create_pull_request_organization(
        self, request: CreatePullReqForOrganization
    ):
        return await self._create_object(
            scheme=CreatePullReqForOrganization, request=request, model=PullRequestModel
        )

    async def _get_repositorys_pull_request(self, repository_id: int):
       
        cached_data = await self.redis_cli.get(f"get-repository-pull-request-{repository_id}")
        if cached_data:
            log.info("Returning data from cache %s", repository_id)

            await publish_message(
                message=json.dumps(jsonable_encoder(cached_data)),
                queues_name=f"get-repository-pull-request-{repository_id}",
                connetcion=self.rmq_cli
            )

            return [PullRequestSchema(**obj) for obj in json.loads(cached_data)]
        
        response = await self._get_objects(
            scheme=PullRequestSchema,
            model=PullRequestModel,
            user_scheme=SUser,
            field=repository_id,
            field_name="repository_id",
        )


        serialized_response = jsonable_encoder(response)


        await publish_message(
            message=json.dumps(serialized_response),
            queues_name=f"get-repository-pull-request-{repository_id}",
            connetcion=self.rmq_cli
        )

        await self.redis_cli.setex(
            f"get-repository-pull-request-{repository_id}", 300, json.dumps(serialized_response)
        )

        return response

    
    async def _update_pull_request(self, request: UpdatePullRequestScheme):
        pull_request = (await self.session.execute(
            select(PullRequestModel)
            .filter_by(id=request.id)
        )).scalars().first()

        if not pull_request:
            raise HTTPException(
                detail="Not Found",
                status_code=404
            )
        await self._request_to_url(f"http://localhost:8081/user/api/v1/get-user/{pull_request.user_id}/")
        user_data = await consume_data(f"get-user-by-id-{pull_request.user_id}", connection=self.rmq_cli)
        user = SUser.parse_obj(user_data)



        for field, value in request.dict(exclude_unset=True).items():
            if (
                field
                in [
                    "status",
                ]
                and value is not None
            ):
                setattr(pull_request, field, value)

        await self._send_message_to_email(letter=f"{request.status}, {request.letter} to {pull_request.repository_id}", email=user.email, subject="Repository Request")
        await self.session.commit()



    async def _create_object(self, request: Type[T], scheme: Type[T], model: Type[T]):
        data = request.dict()
        obj = model(**data, user_id = self.current_user.id)
        self.session.add(obj)
        await self.session.commit()
        return scheme(**request.__dict__)

    async def _get_objects(
        self, scheme: Type[T], model: Type[T], field: Any, field_name: str, user_scheme: Type[T]
    ) -> Optional[List[T]]:

        objects = (
            await self.session.execute(
                select(model).filter(getattr(model, field_name) == field)
            )
        ).scalars().all()


        await asyncio.gather(
            *[
                self._request_to_url(f"http://localhost:8081/user/api/v1/get-user/{obj.user_id}/")
                for obj in objects
            ]
        )


        user_data_json = await asyncio.gather(
            *[
                consume_data(f"get-user-by-id-{obj.user_id}", connection=self.rmq_cli)
                for obj in objects
            ]
        )

        user_schemes = [
            user_scheme(**(data if isinstance(data, dict) else json.loads(data)))
            for data in user_data_json
        ]

        return [
            scheme(**obj.__dict__, user=user)
            for obj, user in zip(objects, user_schemes)
        ]


    async def _send_message_to_email(self, letter, email, subject):
        message = MessageSchema(
            subject = subject,
            recipients=[email],
            body=letter,
            subtype="plain",
        )

        fm = FastMail(conf)
        log.info("Letter succsesfully sended")
        await fm.send_message(message)

        return {"detail": "Sendded Succsesfully"}

    async def _get_data_from_cache(self, key):
        cached_data = await self.redis_cli.get(key)
        if isinstance(cached_data, list):
            return [item for item in json.loads(cached_data)]
        return json.loads(cached_data)

    async def _request_to_url(self, url):
        async with httpx.AsyncClient() as cl:
            response = await cl.get(url)
            return response
