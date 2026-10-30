import aio_pika as pika
import json
import asyncio
from fastapi import FastAPI
from logger import logger
from tasks import r
from storage import cfg, s3
import os

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
    queue=await channel.declare_queue('retry', durable=True, arguments={'x-message-ttl':30000, 'x-dead-letter-routing-key':'images_queue', 'x-dead-letter-exchange':''})
    dlx_queue=await channel.declare_queue('dlx',durable=True)

    async def callback(message:pika.IncomingMessage):
        async with message.process():
            body=json.loads(message.body.decode())
            tries=await r.get(f'{body['id']}')
            tries=int(tries) #type:ignore
            if not tries: 
                await r.set(f'{body['id']}',1)
                tries=1
            try:
                response=s3.get_object(Bucket=cfg.bucket, Key=body['name'])
                image_data=response['Body'].read()
                response.close()
                response.release_conn()
                await r.delete(f'{body['id']}')
                await channel.default_exchange.publish(
                    pika.Message(body=message.body),
                    routing_key='images_queue'
                )
            except Exception as e:
                if tries>3:
                    await r.set(f'{body['id']}',tries+1)
                    await channel.default_exchange.publish(
                        pika.Message(body=message.body),
                        routing_key='dlx'
                    )
                else:
                    await r.set(f'{body['id']}',tries+1)
                    await channel.default_exchange.publish(
                        pika.Message(body=message.body),
                        routing_key='retry'
                    )
    await queue.consume(callback) #type:ignore

@app.on_event('startup')
async def startup():
    logger.info('Retry Worker Started')
    spawn(main())

@app.get('/')
async def root():
    return {'status':'ok'}
