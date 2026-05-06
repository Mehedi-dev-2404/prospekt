from importlib import import_module

import uvicorn
from fastapi import APIRouter, FastAPI

from config import settings


def get_router(module_path: str) -> APIRouter:
    module = import_module(module_path)
    return getattr(module, "router", APIRouter())


app = FastAPI(
    title="Prospekt",
    description="AI-powered lead generation and outreach pipeline",
    version="1.0.0",
)

app.include_router(get_router("routers.pipeline"), prefix="/pipeline", tags=["pipeline"])
app.include_router(get_router("routers.webhooks"), prefix="/webhooks", tags=["webhooks"])


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "app": "Prospekt", "version": "1.0.0"}


@app.on_event("startup")
def startup_event() -> None:
    print("Prospekt is running")


if __name__ == "__main__":
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
