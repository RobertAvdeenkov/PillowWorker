import pytest_asyncio
import httpx
from models import Base,User,Image,ReferenceImage
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy import create_engine,delete
from main import app
from database import get_db
from sqlalchemy.orm import sessionmaker
from auth import create_token
from datetime import timedelta
import io

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

async def fetch(url,type, data=None, json=False, cookies=None,file=None):
    transport=httpx.ASGITransport(app)
    async with httpx.AsyncClient(transport=transport, base_url='http://127.0.0.1') as client:
        if type=='get':
            response=await client.get(url, cookies=cookies if cookies else {})
            return (response.status_code, response.json() if json else None)
        elif type=='post':
            response=await client.post(url,data=data, cookies=cookies if cookies else {}, files=file if file else {})
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

async def test_upload():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    with open('image.jpg', 'rb') as file:
        content=file.read()
    data=io.BytesIO(content)
    response=await fetch('/upload', 'post', cookies={'access_token':create_token('test',timedelta(hours=1))}, file={'file':('image.jpg', data,'image/jpg')}, data={'filter':'grayscale'}, json=True)
    assert response[0]==200 #type:ignore

async def test_load_images():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    response=await fetch('/images','get',cookies={'access_token':create_token('test',timedelta(hours=1))})
    assert response[0]==200 #type:ignore

async def test_load_refimages():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    response=await fetch('/refimages','get',cookies={'access_token':create_token('test',timedelta(hours=1))})
    assert response[0]==200 #type:ignore

async def test_delete_original():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    with open('image.jpg', 'rb') as file:
        content=file.read()
    data=io.BytesIO(content)
    await fetch('/upload', 'post', cookies={'access_token':create_token('test',timedelta(hours=1))}, file={'file':('image.jpg', data,'image/jpg')}, data={'filter':'grayscale'}, json=True)
    response=await fetch('/images/1','delete',cookies={'access_token':create_token('test',timedelta(hours=1))})
    assert response[0]==200 #type:ignore

async def test_logout():
    await fetch('/reg', 'post', {'name':'test','password':'123'})
    await fetch('/login', 'post', {'name':'test','password':'123'})
    response=await fetch('/logout','get')
    assert response[0]==303 #type:ignore
