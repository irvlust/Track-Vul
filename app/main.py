from fastapi import FastAPI
from app.api.routes_applications import router as app_router

app = FastAPI(title="Track Vul API")
app.include_router(app_router)