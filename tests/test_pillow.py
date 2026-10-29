import pytest_asyncio
import httpx
from models import Base,User,Image,ReferenceImage
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy import create_engine,delete
from main import app
from database import get_db
from sqlalchemy.orm import sessionmaker

client=TestClient(app)

engine=create_async_engine('sqlite+aiosqlite:///test_images.db')
sync_engine=create_engine('sqlite:///test_images.db')
Base.metadata.create_all(sync_engine)

TestSessionLocal=sessionmaker(engine,class_=AsyncSession, expire_on_commit=False) #type:ignore

async def get_over_db():
    async with TestSessionLocal() as db: #type:ignore
        try:
            yield db
        finally:
            await db.close()

app.dependency_overrides[get_db]=get_over_db

async def fetch(url,type, data=None, json=False, cookies=None):
    transport=httpx.ASGITransport(app)
    async with httpx.AsyncClient(transport=transport, base_url='http://127.0.0.1') as client:
        if type=='get':
            response=await client.get(url, cookies=cookies if cookies else {})
            return (response.status_code, response.json() if json else None)
        elif type=='post':
            response=await client.post(url,data=data, cookies=cookies if cookies else {})
            return (response.status_code, response.json() if json else None)
        elif type=='delete':
            response=await client.delete(url, cookies=cookies if cookies else {})
            return (response.status_code, response.json() if json else None)

@pytest_asyncio.fixture
async def db():
    async with TestSessionLocal() as con: #type:ignore
        try:
            yield con
        finally:
            await con.close()

@pytest_asyncio.fixture(autouse=True)
async def clean_db(db):
    await db.execute(delete(User))
    await db.execute(delete(Image))
    await db.execute(delete(ReferenceImage))
    await db.commit()
    yield

async def test_reg():
    response=await fetch('/reg', 'post', {'name':'test','password':'123'})
    assert response[0]==303 #type:ignore

async def test_login():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    response=await fetch('/login', 'post', {'name':'test','password':'123'})
    assert response[0]==303 #type:ignore

async def test_wrong_reg():
    response=await fetch('/reg', 'post', {'name':'test','password':'123'})
    response=await fetch('/reg', 'post', {'name':'test','password':'1234'})
    assert response[0]==409 #type:ignore

async def test_wrong_login():
    response=await fetch('/reg', 'post', {'name':'test','password':'123'})
    response=await fetch('/reg', 'post', {'name':'test','password':'1234'})
    assert response[0]==409 #type:ignore

