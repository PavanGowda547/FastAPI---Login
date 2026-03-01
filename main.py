from fastapi import FastAPI
from routers.auth_routes import router

app = FastAPI()
app.include_router(router)