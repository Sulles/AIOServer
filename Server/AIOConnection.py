"""
AIO Connection Object
"""

import trio

from uuid import UUID
from .util import ServiceRequestEvent
from CommonLib.proto.AIOMessage_pb2 import AIOMessage


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
        """
        AIOConnection receiver
        - Should only receive (potentially encrypted) AIOMessages
        """
        try:
            async for serialized_aio_message in self._connection_stream:
                aio_message = AIOMessage()
                aio_message.ParseFromString(serialized_aio_message)
                print(f'AIOConnection:{self._uuid.hex[:8]} got data: {aio_message}')
                await self._server_event_handler(
                    self.aio_msg_to_service_request(
                        self.decrypt(aio_message)))

        except trio.BrokenResourceError as e:
            print(f'{e}')

    def decrypt(self, aio_message: AIOMessage) -> AIOMessage:
        """
        TODO: Convert encrypted_message to message
        :param aio_message:
        """
        return aio_message

    def aio_msg_to_service_request(self, aio_message: AIOMessage) -> ServiceRequestEvent:
        """
        Convert a received and decrypted AIOMessage into a ServiceRequestEvent
        :param aio_message: Decrypted AIOMessage received from a client
        """
        return ServiceRequestEvent(
            service_name=aio_message.message_name,
            service_message=aio_message.message,
            response_callback=self.send)

    async def send(self, data: bytes):
        """ AIOConnection sender """
        await self._connection_stream.send_all(data)
