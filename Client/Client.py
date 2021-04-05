"""
Client object
"""

import asyncio


HOST = '127.0.0.1'
PORT = 8888


async def connect():
    rx, tx = await asyncio.open_connection(HOST, PORT)
    while True:
        outbound_message = input('Send something to server: ')
        tx.write(outbound_message.encode('utf-8'))
        # await tx.drain()
        inbound_message = await rx.read()
        print(f'Got inbound message: {inbound_message.decode("utf-8")}')


if __name__ == '__main__':
    try:
        asyncio.run(connect())

    except KeyboardInterrupt:
        print(f'--- KEYBOARD INTERRUPT ---')
