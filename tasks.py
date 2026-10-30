from fastapi.routing import APIRouter
from database import get_db
from fastapi import Depends,Cookie,Form,HTTPException, UploadFile
from logger import logger
from auth import create_token,get_user
import redis.asyncio as redis
import aio_pika as pika
import json
from sqlalchemy.ext.asyncio import AsyncSession
import bcrypt
from fastapi.responses import RedirectResponse,FileResponse,JSONResponse,Response
from sqlalchemy import select
from models import User,Image,ReferenceImage
from datetime import timedelta
import os
from storage import s3,cfg
import io

router=APIRouter()

REDIS_URL=os.getenv('REDIS_URL')
if REDIS_URL: r=redis.from_url(REDIS_URL,decode_responses=True)
else: r=redis.Redis(decode_responses=True)

async def get_channel():
    connection=await pika.connect_robust(os.getenv('RABBITMQ_URL',None))
    channel=await connection.channel()
    yield channel

@router.get('/')
async def login():
    return FileResponse('templates/login.html')

@router.get('/register')
async def register():
    return FileResponse('templates/register.html')

@router.get('/mainpage')
async def mainpage():
    return FileResponse('templates/mainpage.html')

@router.post('/reg')
async def reg(name=Form(min_length=3, max_length=30), password=Form(), db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==name))).first()
    if result:
        raise HTTPException(409,'Такой пользователь уже есть!')
    target=User(name=name,password=bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode())
    db.add(target)
    await db.commit()
    logger.info(f'New user: {name}')
    return RedirectResponse('/',status_code=303)

@router.post('/login')
async def log_in(name=Form(), password=Form(), db:AsyncSession=Depends(get_db)):
    result=(await db.execute(select(User).filter(User.name==name))).first()
    if not(result):
        raise HTTPException(401,'Неправильный логин или пароль!')
    user=result[0]
    if not(bcrypt.checkpw(password.encode(), user.password.encode())):
        raise HTTPException(401,'Неправильный логин или пароль!')
    response=RedirectResponse('/mainpage', status_code=303)
    refresh=create_token(user.name,timedelta(days=30))
    response.set_cookie('access_token', create_token(user.name,timedelta(hours=1)), max_age=3600,path='/')
    response.set_cookie('refresh_token', refresh, max_age=3600*24*30,path='/')
    user.refresh_token=refresh
    await db.commit()
    return response

@router.post('/refresh')
async def refresh(refresh_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(refresh_token)
    if user.refresh_token!=refresh_token:
        raise HTTPException(401,'Неправильный токен!')
    response=JSONResponse({'status':'ok'})
    response.set_cookie('access_token',create_token(user.name, timedelta(hours=1)),path='/', max_age=3600)
    return response

@router.get('/logout')
async def logout():
    response=RedirectResponse('/',status_code=303)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

@router.post('/upload')
async def upload(file:UploadFile, db:AsyncSession=Depends(get_db), access_token=Cookie(), channel=Depends(get_channel), filter=Form()):
    user=await get_user(access_token)
    if not(file.filename.endswith('.jpg') or file.filename.endswith('.jpeg')): #type:ignore
        raise HTTPException(400,'Недопустимый формат изображения!')
    content=await file.read()
    target=Image(filename=file.filename, user_id=user.id)
    db.add(target)
    await db.commit()
    await db.refresh(target)
    name=f'{user.name}/{target.id}.jpg'
    s3.put_object(Bucket=cfg.bucket,Key=name, Body=io.BytesIO(content), ContentType='image/jpeg')
    await channel.default_exchange.publish(routing_key='images_queue', message=pika.Message(json.dumps({'id':target.id, 'filter':filter, 'name':name, 'username':user.name, 'user_id':user.id, 'filename':file.filename}).encode()))
    await r.delete(f'{user.name}:images')

@router.get('/images')
async def load_images(access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(access_token)
    data=await r.get(f'{user.name}:images')
    if data:
        return {'images': json.loads(data)}
    result=(await db.execute(select(Image).filter(Image.user_id==user.id))).all()
    all_fotos=[]
    for i in result:
        foto=i[0]
        all_fotos.append({'id':foto.id,'status':foto.status, 'filename':foto.filename,'created_at':foto.created_at.strftime("%Y-%m-%d %H:%M:%S")})
    await r.setex(f'{user.name}:images',60, json.dumps(all_fotos))
    return {'images':all_fotos}

@router.get('/refimages')
async def load_ref(access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(access_token)
    data=await r.get(f'{user.name}:refimages')
    if data: return {'images':json.loads(data)}
    result=(await db.execute(select(ReferenceImage).filter(ReferenceImage.user_id==user.id))).all()
    all_fotos=[]
    for i in result:
        foto=i[0]
        all_fotos.append({'id':foto.id,'size':foto.size, 'filename':foto.url})
    await r.setex(f'{user.name}:refimages',60, json.dumps(all_fotos))
    return {'images':all_fotos}


@router.delete('/images/{id}')
async def delete_image(id:int,access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(access_token)
    result=(await db.execute(select(Image).filter(Image.id==id))).first()
    if not result:
        raise HTTPException(404,'Такого изображения нет!')
    target=result[0]
    if user.id==target.user_id:
        await db.delete(target)
        await db.commit()
        await r.delete(f'{user.name}:images')
        await r.delete(f'{user.name}:refimages')
    else:
        raise HTTPException(404,'Такого изображения нет!')

@router.delete('/reference/{id}')
async def delete_reference(id:int,access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(access_token)
    result=(await db.execute(select(ReferenceImage).filter(ReferenceImage.id==id))).first()
    if not result:
        raise HTTPException(404,'Такого изображения нет!')
    target=result[0]
    if user.id==target.user_id:
        await db.delete(target)
        await db.commit()
        await r.delete(f'{user.name}:refimages')
    else:
        raise HTTPException(404,'Такого изображения нет!')

@router.get('/images/{name}')
async def get_image(name:str, access_token=Cookie(), db:AsyncSession=Depends(get_db)):
    user=await get_user(access_token)
    result=(await db.execute(select(ReferenceImage).filter(ReferenceImage.url==name))).first()
    if not result: raise HTTPException(404,'Такого изображения нет!')
    target=result[0]
    if target.user_id!=user.id: raise HTTPException(404,'Такого изображения нет!')
    data=await r.get(f'image:{name}')
    if data: return Response(data, media_type='image/jpeg')
    image=s3.get_object(Bucket=cfg.bucket,Key=name)
    image_data=image['Body'].read()
    await r.set(f'image:{name}', image_data)
    return Response(image_data, media_type='image/jpeg')
