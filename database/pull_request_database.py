from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config.config import db_settings


DATABASE_URL = f"postgresql+asyncpg://{db_settings.username}:{db_settings.password.get_secret_value()}@{db_settings.host}:{db_settings.port}/PullRequestDB"

pull_req_engine = create_async_engine(DATABASE_URL)

async_session = sessionmaker(class_=AsyncSession, expire_on_commit=pull_req_engine, bind=pull_req_engine)

class PullRequestBASE(DeclarativeBase):
    pass

async def get_pull_request_sesison() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
