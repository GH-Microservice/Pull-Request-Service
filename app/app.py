from fastapi import FastAPI
from apps.pull_request.router import pull_request_service_router
from database.pull_request_database import pull_req_engine, PullRequestBASE


app = FastAPI(title="Pull Requests Service API")

app.include_router(pull_request_service_router)


async def create_teables():
    async with pull_req_engine.begin() as conn:
        await conn.run_sync(PullRequestBASE.metadata.create_all)


@app.on_event("startup")
async def on_startup():
    return await create_teables()
