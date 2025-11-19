from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.router_collector import get_api_routers
from config.settings import settings
from common.exceptions.handlers import register_exception_handlers
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI()
origins = settings.ALLOWED_ORIGINS.split(',') if settings.ALLOWED_ORIGINS else []

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in get_api_routers():
    app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Hello FastAPI"}