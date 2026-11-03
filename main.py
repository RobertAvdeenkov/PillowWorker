from fastapi.staticfiles import StaticFiles
from database import engine
from logger import logger
from models import Base
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from tasks import router,r
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

@app.middleware('http')
async def rate_limit(request:Request, call_next):
    client=request.scope.get('client')
    f=request.headers.get('X-Forwarded-For')
    ip=f.split(',')[0].strip() if f else (client[0] if client else 'unknown')
    data=await r.get(f'{ip}:{request.url.path}')
    if data:
        data=int(data)+1
    else: data=1
    if data>3: return JSONResponse({'message':'Слишком много запросов!'}, status_code=429)
    else: await r.setex(f'{ip}:{request.url.path}',60,str(data))
    response=await call_next(request)
    return response

app.include_router(router)