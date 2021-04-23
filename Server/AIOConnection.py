"""
AIO Connection Object
"""

import trio

from uuid import UUID
from .util import ServiceRequestEvent
from google.protobuf.message import Message
from CommonLib.proto.Base_pb2 import EncryptionType, PublicRSAKey, AESKey
from CommonLib.proto.AIOMessage_pb2 import AIOMessage
from CommonLib.proto.Authenticator_pb2 import IPCAuthenticatorUpdate


class AIOConnection:
    def __init__(self, uuid: UUID, connection_stream: trio.SocketStream,
                 server_event_handler: trio.abc.SendChannel.send):
        """
        :param uuid:
        :param connection_stream:
        :param server_event_handler:
        """
        # General information
        self._is_alive = True
        self._uuid = uuid

        # Connection stream and server event handler
        self._connection_stream = connection_stream
        self._server_event_handler = server_event_handler

        # Internal functionality
        self._active_encryption_method: str = 'PLAIN_TEXT'
        self.__aes_key = None   # TODO: Create AES key object
        self.__rsa_key = None   # TODO: Create RSA key object
        self._internal_callback_handler: dict[str: classmethod] = dict(
            IPCAuthenticatorUpdate=self._handle_ipc_authenticator_update
        )

    def __str__(self):
        return f'[AIOConnection:{self._uuid}; EncryptionType:{self._active_encryption_method}]'

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
                    self._aio_msg_to_service_request(
                        self._decrypt(aio_message)))

        except trio.BrokenResourceError as e:
            print(f'{e}')

    def _decrypt(self, aio_message: AIOMessage) -> AIOMessage:
        """
        TODO: Convert encrypted_message to message
        :param aio_message:
        """
        return aio_message

    def _encrypt(self, aio_message: AIOMessage) -> AIOMessage:
        """
        TODO: Convert plaintext AIOMessage to encrypted message
        :param aio_message:
        """
        return aio_message

    def _aio_msg_to_service_request(self, aio_message: AIOMessage) -> ServiceRequestEvent:
        """
        Convert a received and decrypted AIOMessage into a ServiceRequestEvent
        :param aio_message: Decrypted AIOMessage received from a client
        """
        return ServiceRequestEvent(
            service_name=aio_message.message_name,
            service_message=aio_message.message,
            response_callback=self.send,
            originator_callback=self.handle_callback)

    async def handle_callback(self, aio_message: AIOMessage) -> None:
        """ AIOConnection object callback """
        if aio_message.message_name in self._internal_callback_handler.keys():
            # PyCharm doesn't like reference maps...
            # noinspection PyArgumentList
            self._internal_callback_handler[aio_message.message_name](aio_message.message)

    def _handle_ipc_authenticator_update(self, message: bytes):
        """ IPCAuthenticatorUpdate handler """
        ipc_auth_message = IPCAuthenticatorUpdate()
        ipc_auth_message.ParseFromString(message)
        print(f'Got IPCAuthenticatorUpdate: {ipc_auth_message}')
        self._active_encryption_method = EncryptionType.Name(ipc_auth_message.set_encryption_type)
        if self._active_encryption_method == 'RSA' and ipc_auth_message.rsa_key:
            self.__update_rsa_key(ipc_auth_message.rsa_key)
        elif self._active_encryption_method == 'AES' and ipc_auth_message.aes_key:
            self.__update_aes_key(ipc_auth_message.aes_key)
        print(self)

    def __update_rsa_key(self, rsa_key: PublicRSAKey):
        """ Update internal RSA key with new key """
        raise NotImplemented

    def __update_aes_key(self, aes_key: AESKey):
        """ Update internal AES key with new key """
        raise NotImplemented

    async def send(self, message: Message):
        """ AIOConnection _sender """
        aio_wrapper = AIOMessage()
        aio_wrapper.message_name = message.DESCRIPTOR.name
        aio_wrapper.message = message.SerializeToString()
        aio_wrapper = self._encrypt(aio_wrapper)
        print(f'{self} sending message: {aio_wrapper}')
        await self._connection_stream.send_all(
            aio_wrapper.SerializeToString())
