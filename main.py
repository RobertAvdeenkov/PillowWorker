from fastapi.staticfiles import StaticFiles
from database import engine
from logger import logger
from models import Base
from storage import add_bucket
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tasks import router

app=FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://127.0.0.1:8000','https://pillowworker.onrender.com'],
    allow_methods=['GET',"POST",'DELETE'],
    allow_headers=['*']
)

@app.on_event('startup')
async def startup():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)
    add_bucket()
    logger.info('Main app started')

app.include_router(router)