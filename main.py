from fastapi.staticfiles import StaticFiles
from database import engine
from logger import logger
from models import Base
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from tasks import router
from time import time
from prometheus_client import Counter, make_asgi_app, Histogram

REQUEST_COUNTER=Counter('http_couter', 'HTTP COUNTER', ['method','endpoint','status'])
REQUEST_LATENCY=Histogram('http_latency','HTTP latency',['method','endpoint'])
metrics_app=make_asgi_app()

app=FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount('/metrics',metrics_app)

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
    logger.info('Main app started')

@app.middleware('http')
async def metrics(request:Request, call_next):
    start=time()
    response=await call_next(request)
    duration=time() - start

    REQUEST_COUNTER.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(duration)

    return response

app.include_router(router)