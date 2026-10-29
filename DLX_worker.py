import asyncio
import json
import os
import aio_pika as pika
from fastapi import FastAPI
from sqlalchemy import text
from database import SessionLocal
from logger import logger

app=FastAPI()
background_tasks = set()

def spawn(coro):
    t = asyncio.create_task(coro)
    background_tasks.add(t)
    t.add_done_callback(background_tasks.discard)
    return t

async def main():
    connection=await pika.connect_robust(os.getenv('RABBITMQ_URL',None))
    channel=await connection.channel()
    queue=await channel.declare_queue('dlx',durable=True)

    async def callback(message:pika.IncomingMessage):
        async with message.process():
            body=json.loads(message.body.decode())
            async with SessionLocal() as db: #type:ignore
                await db.execute(text('''
                UPDATE images SET status=\'failed\' WHERE id=:image_id
                '''), {'image_id':body['id']})
                await db.commit()

    await queue.consume(callback) #type:ignore
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        return

@app.on_event('startup')
async def startup():
    logger.info('DLX Worker Started')
    spawn(main())

@app.get('/')
async def root():
    return {'status':'ok'}
