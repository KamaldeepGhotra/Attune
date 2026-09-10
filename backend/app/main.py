from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.routers import auth, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Attune", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(recommendations.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
