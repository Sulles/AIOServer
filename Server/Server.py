"""
----------------------------------------------------------------------------------------------------
    Server
----------------------------------------------------------------------------------------------------
Description: The actual server
Responsibilities:
    - Entry point for all client communication
    - Client connection registrar
    - Service registrar
    - Routing point for client connections and services
"""

from uuid import uuid1, UUID

import trio

from .AIOConnection import AIOConnection
from .util import ServiceRequestEvent

HOST = ''
PORT = 8888


class Server:
    """ Define member variables """
    tx_event_channel: trio.abc.SendChannel
    rx_event_channel: trio.abc.ReceiveChannel

    def __init__(self):
        """ Server initializer """
        self._is_alive = False
        self._connections: dict[UUID.hex, AIOConnection] = dict()
        self._service_map: dict[str, trio.lowlevel.wait_writable] = dict()
        self.services: list[object] = list()

    @property
    def is_alive(self):
        return self._is_alive

    def register_service(self, service_name: str,
                         service_callable: trio.lowlevel.wait_writable) -> None:
        """
        Register a service in Server
        :param service_name:
        :param service_callable:
        """
        if service_name in self._service_map.keys():
            raise (NameError, f'Conflicting service "{service_name}" already registered!')
        else:
            self._service_map[service_name] = service_callable

    def _start_all_services(self):
        """ Start all Services in the services folder """
        print(f'Starting all services...')
        server_module = __import__('Server.services')
        all_service_files = server_module.__dict__['services'].__dict__['__all__']
        print(f'All service files: {all_service_files}')
        for service_file in all_service_files:
            service_module = __import__(f'Server.services.{service_file}')
            # All service objects must be named identically to the file that they are saved under
            service_module = service_module.__dict__['services'].__dict__[service_file]
            service_class = getattr(service_module, service_file)
            # All service classes must be initialize themselves with register callback
            #   in order to map Message object names to Service object handlers
            self.services.append(service_class(self.register_service))
        [print(f'Added {_} to server services list') for _ in self.services]

    async def _handle_new_connection(self, connection_stream):
        """ Handle new connection """
        print('Server received new connection!')

        # Create unique uuid for new AIOConnection
        uuid = uuid1()
        self._connections[uuid.hex] = \
            AIOConnection(uuid, connection_stream, self.tx_event_channel.send)

        # Add AIOConnection main runner to nursery
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self._connections[uuid.hex].receiver)

    async def _event_processor(self):
        """ Server event processor """
        async for event in self.rx_event_channel:
            if isinstance(event, ServiceRequestEvent):
                print(f'Server got ServiceRequestEvent!\n{event}')
                try:
                    await self._service_map[event.service_name](event)
                except Exception as e:
                    print(f'CRITICAL ERROR: {e}')
            else:
                print(f'Server got unsupported event: {event}')
            # TODO: 1. Create ticket for event
            # TODO: 2. Process event
            # TODO: 3. Close ticket for event

    async def run(self):
        """ Main Server run method """
        if self.is_alive:
            raise (RuntimeError, 'Server already running!')
        else:
            self._is_alive = True
        print('Starting Server...')

        # Open nursery
        async with trio.open_nursery() as nursery:
            # Create server event _sender/_receiver channel
            self.tx_event_channel, self.rx_event_channel = trio.open_memory_channel(0)

            # Start Server event processor
            nursery.start_soon(self._event_processor)

            # Start all services
            self._start_all_services()

            # Create TCP listener(s)
            tcp_listeners = await trio.open_tcp_listeners(port=PORT, host=HOST)
            print(f'Server listening or connections on {HOST}:{PORT}')

            # Add Server handler for new connections
            await trio.serve_listeners(
                handler=self._handle_new_connection,
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
