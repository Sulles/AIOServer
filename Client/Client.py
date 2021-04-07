import sys

import trio

HOST = '127.0.0.1'
PORT = 8888


class Client:
    def __init__(self):
        pass

    async def sender(self, client_stream):
        print("sender: started!")
        while True:
            data = input('> ').encode('utf-8')
            print(f"sender: sending {data!r}")
            await client_stream.send_all(data)
            await trio.sleep(0.01)

    async def receiver(self, client_stream):
        print("receiver: started!")
        async for data in client_stream:
            print(f"receiver: got data {data!r}")
        print("receiver: connection closed")
        sys.exit()

    async def run(self):
        print(f"client: connecting to {HOST}:{PORT}")
        client_stream = await trio.open_tcp_stream(HOST, PORT)
        async with client_stream:
            async with trio.open_nursery() as nursery:
                print("client: spawning sender...")
                nursery.start_soon(self.sender, client_stream)

                print("client: spawning receiver...")
                nursery.start_soon(self.receiver, client_stream)

    def cleanup(self):
        """ Client graceful cleanup and terminate """
        # TODO: this...
        pass


if __name__ == '__main__':
    client = Client()

    try:
        trio.run(client.run)

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    client.cleanup()
