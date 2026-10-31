from aiogram import Bot,Dispatcher,types,F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from database import SessionLocal
from sqlalchemy import select
from models import User,Image
import bcrypt
from fastapi import FastAPI
import asyncio
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logger import logger
from storage import cfg, s3
import aio_pika as pika
import io
import json

connection=None
channel=None

app=FastAPI()

class Form(StatesGroup):
    waiting_for_login = State()
    waiting_for_password = State()

Token=os.getenv('TOKEN', '')

background_tasks = set()

def spawn(coro):
    t = asyncio.create_task(coro)
    background_tasks.add(t)
    t.add_done_callback(background_tasks.discard)
    return t

bot=Bot(token=Token)
dp=Dispatcher()

@dp.message(Command('start'))
async def start(message:types.Message,state:FSMContext):
    data=await state.get_data()
    username=data.get('username')
    if username:
        builder=InlineKeyboardBuilder()
        builder.button(text='Выйти из аккаунта',callback_data='logout')
        builder.adjust(1)
        txt=f'Здравствуйте, {username}!\nЧтобы наложить эффект, пришлите фото.\nК фотографии прикрепите название одного из фильтров:\ngrayscale\nblur\nsharpen\nБольше опций на сайте: https://pillowworker.onrender.com/'
        await message.answer(text=txt, reply_markup=builder.as_markup())
        return
    else:
        await message.answer('Введите логин:')
        await state.set_state(Form.waiting_for_login)

@dp.message(Form.waiting_for_login)
async def after_login(message:types.Message,state:FSMContext):
    await state.update_data(login=message.text)
    await message.answer('Введите пароль:')
    await state.set_state(Form.waiting_for_password)

@dp.message(Form.waiting_for_password)
async def after_password(message:types.Message,state:FSMContext):
    data=await state.get_data()
    login=data.get('login')
    if login:
        async with SessionLocal() as db: #type:ignore
            result=(await db.execute(select(User).filter(User.name==login))).first()
            if not result:
                await message.answer('Неправильный логин или пароль!')
                return
            user=result[0]
            if not(bcrypt.checkpw(message.text.encode(), user.password.encode())): #type:ignore
                await message.answer('Неправильный логин или пароль!')
                return
            user.tg_id=str(message.from_user.id) #type:ignore
            await state.update_data(username=login)
            await state.set_state(None)
            await message.answer('Успешно!\nНажмите /start, чтобы продолжить')
            return
    else:
        await message.answer('Нажмите /start, чтобы продолжить')
        return

@dp.message(F.data=='logout')
async def logout(message:types.Message,state:FSMContext):
    await state.clear()
    await message.answer('Вы вышли из аккаунта.\nНажмите /start, чтобы продолжить')
    return

@dp.message(F.photo)
async def apply_filter(message:types.Message,state:FSMContext):
    global connection,channel
    current_state = await state.get_state()
    if current_state is not None:
        await message.answer("Сначала завершите вход или нажмите /start")
        return
    data=await state.get_data()
    username=data.get('username')
    if username:
        async with SessionLocal() as db: #type:ignore
            result=(await db.execute(select(User).filter(User.name==username))).first()
            if not result:
                await message.answer('Произошла ошибка!')
                return
        user=result[0]
        photo = message.photo[-1] #type:ignore
        file_in_memory = await message.bot.download(photo) #type:ignore
        image_bytes = file_in_memory.read() #type:ignore
        target=Image(filename=file_in_memory.name, user_id=user.id) #type:ignore
        db.add(target)
        await db.commit()
        await db.refresh(target)
        name=f'{user.name}/{target.id}.jpg'
        s3.put_object(Bucket=cfg.bucket,Key=name, Body=io.BytesIO(image_bytes), ContentType='image/jpeg')
        await channel.default_exchange.publish(routing_key='images_queue', message=pika.Message(json.dumps({'id':target.id, 'filter':message.caption or 'none', 'name':name, 'username':user.name, 'user_id':user.id, 'filename':file_in_memory.name, 'tg_id':message.from_user.id}).encode())) #type:ignore
        await message.answer('Подождите, началась обработка...')
        return
    else:
        await message.answer('Вы не вошли в аккаунт!')
        return

@app.on_event('startup')
async def startup():
    global connection,channel
    logger.info('TG bot started')
    connection=await pika.connect_robust(os.getenv('RABBITMQ_URL',None))
    channel=await  connection.channel()
    await bot.delete_webhook(drop_pending_updates=True)
    spawn(dp.start_polling(bot))

@app.on_event('shutdown')
async def shutdown():
    global connection
    if connection:
        await connection.close()

@app.get('/')
async def root():
    return {'status':'ok'}