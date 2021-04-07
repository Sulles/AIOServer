"""
Server object
"""

import trio

from CommonLib.AIOConnection import AIOConnection
from uuid import uuid1, UUID


HOST = '127.0.0.1'
PORT = 8888


class Server:
    """ Define member variables """
    tx_event_channel: trio.abc.SendChannel
    rx_event_channel: trio.abc.ReceiveChannel

    def __init__(self):
        """ Server initializer """
        self._is_alive = True
        self._connections: dict[UUID.hex, AIOConnection] = dict()

    @property
    def is_alive(self):
        return self._is_alive

    async def handle_new_connection(self, connection_stream):
        """ Handle new connection """
        print('Server received new connection!')

        # Create unique uuid for new AIOConnection
        uuid = uuid1()
        self._connections[uuid.hex] = \
            AIOConnection(uuid, connection_stream, self.tx_event_channel.send)

        # Add AIOConnection main runner to nursery
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._connections[uuid.hex].receiver)

    async def event_processor(self):
        """ Server event processor """
        async for event in self.rx_event_channel:
            print(f'Server got event! {event}')

    async def run(self):
        """ Main Server run method """
        print('Starting Server...')

        # Open nursery
        async with trio.open_nursery() as nursery:

            # Create server event sender/receiver channel
            self.tx_event_channel, self.rx_event_channel = trio.open_memory_channel(0)

            # Start Server event processor
            nursery.start_soon(self.event_processor)

            # Create TCP listener(s)
            tcp_listeners = await trio.open_tcp_listeners(port=PORT, host=HOST)
            print(f'Server listening or connections on {HOST}:{PORT}')

            # Add Server handler for new connections
            await trio.serve_listeners(
                handler=self.handle_new_connection,
                listeners=tcp_listeners,
                handler_nursery=nursery)

    def cleanup(self):
        """ Server graceful cleanup and terminate """
        # TODO: this...
        pass


if __name__ == '__main__':
    my_server = Server()

    try:
        trio.run(my_server.run)

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    finally:
        my_server.cleanup()
