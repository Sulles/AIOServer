"""
AIO Connection Object
"""

import trio

from uuid import UUID
from CommonLib.Events import TextEvent


class AIOConnection:
    def __init__(self, uuid: UUID, connection_stream: trio.SocketStream,
                 server_event_handler: trio.abc.SendChannel.send):
        """
        :param uuid:
        :param connection_stream:
        :param server_event_handler:
        """
        self._is_alive = True
        self._uuid = uuid
        self._connection_stream = connection_stream
        self._server_event_handler = server_event_handler

    @property
    def is_alive(self):
        return self._is_alive

    async def receiver(self):
        """ AIOConnection receiver """
        try:
            async for data in self._connection_stream:
                print(f'AIOConnection:{self._uuid.hex[:8]} got data: {data}')
                await self._server_event_handler(
                    TextEvent(f'{self._uuid.hex} {data}'))
        except trio.BrokenResourceError as e:
            print(f'{e}')

    async def send(self, data: bytes):
        """ AIOConnection sender """
        await self._connection_stream.send_all(data)
