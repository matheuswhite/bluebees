import asyncio


async def wakeup():
    while True:
        await asyncio.sleep(.1)
