"""
AIO Connection Object
"""

import trio

from uuid import UUID
from .util import ServiceMessageEvent
from google.protobuf.message import Message
from CommonLib.proto.AIOMessage_pb2 import AIOMessage


class AIOConnection:
    def __init__(self, uuid: UUID, connection_stream: trio.SocketStream,
                 server_event_handler: trio.abc.SendChannel.send):
        """
        :param uuid:
        :param connection_stream:
        :param server_event_handler:
        """
        # General information
        self._is_alive: bool = True
        self._uuid: UUID = uuid
        self._username: str = ''

        # Connection stream and server event handler
        self._connection_stream: trio.SocketStream = connection_stream
        self._server_event_handler: trio.abc.SendChannel.send = server_event_handler

    def __str__(self):
        return f'[AIOConnection:{self._uuid}]'

    @property
    def is_alive(self):
        return self._is_alive

    async def receiver(self):
        """
        AIOConnection _receiver
        - Should only receive (potentially encrypted) AIOMessages
        """
        try:
            async for serialized_aio_message in self._connection_stream:
                aio_message = AIOMessage()
                aio_message.ParseFromString(serialized_aio_message)
                print(f'AIOConnection:{self._uuid.hex[:8]} got data: {aio_message}')
                await self._server_event_handler(
                    self._aio_msg_to_service_request(aio_message))

        except trio.BrokenResourceError as e:
            print(f'{e}')

    def _aio_msg_to_service_request(self, aio_message: AIOMessage) -> ServiceMessageEvent:
        """
        Convert a received and decrypted AIOMessage into a ServiceRequestEvent
        :param aio_message: Decrypted AIOMessage received from a client
        """
        return ServiceMessageEvent(
            requester_uuid=self._uuid.int,
            service_name=aio_message.message_name,
            message=aio_message.message,
            response_callback=self.send)

    async def send(self, message: Message):
        """ AIOConnection _sender """
        aio_wrapper = AIOMessage()
        aio_wrapper.message_name = message.DESCRIPTOR.name
        aio_wrapper.message = message.SerializeToString()
        print(f'{self} sending message: {aio_wrapper}')
        await self._connection_stream.send_all(
            aio_wrapper.SerializeToString())
