"""

Client Object
"""

import trio

from google.protobuf.message import Message

from CommonLib.proto.Base_pb2 import ClientInfo
from CommonLib.proto.AIOMessage_pb2 import AIOMessage
from CommonLib.proto.TUIMessage_pb2 import TUIMessage

HOST = '127.0.0.1'
PORT = 8888
TUI_HISTORY_LENGTH = 10


class ClientTerminationEvent(BaseException):
    """ Any Client termination-causing event """
    pass


class Client:
    """
    Client connection to AIOServer
    """
    tx_send_server_channel: trio.abc.SendChannel[AIOMessage]
    rx_send_server_channel: trio.abc.ReceiveChannel[AIOMessage]

    def __init__(self):
        self._is_alive = True
        self.username = input('Username: ')
        # self.__pwd = getpass('Password: ')    # TODO: implement with encryption
        self._service_map: dict[str, classmethod] = dict()
        self.services: list[object] = list()

    @property
    def is_alive(self):
        return self.is_alive

    def register_service(self, service_name: str, service_callback: classmethod):
        """
        Register a service in Client
        :param service_name:
        :param service_callback:
        """
        if service_name in self._service_map.keys():
            raise (NameError, f'Conflicting service "{service_name}" already registered!')
        else:
            self._service_map[service_name] = service_callback
        print(f'Client service map:\n{self._service_map}')
        input()

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

    async def _sender(self, client_stream):
        """
        Sender monitors rx_send_server_channel for AIOMessages to serialize and send to Server
        """
        print("_sender: started!")
        async for aio_msg in self.rx_send_server_channel:
            # print(f"_sender: sending {aio_msg}")
            await client_stream.send_all(aio_msg.SerializeToString())

    async def _receiver(self, client_stream):
        """ Receiver """
        # TODO: Finalize this for generic Client use
        print("_receiver: started!")
        async for data in client_stream:
            print(f"_receiver: got data {data!r}")
        print("_receiver: connection closed")
        raise ClientTerminationEvent

    async def run(self):
        print(f"client: connecting to {HOST}:{PORT}")
        client_stream = await trio.open_tcp_stream(HOST, PORT)
        self.tx_send_server_channel, self.rx_send_server_channel = trio.open_memory_channel(0)
        async with client_stream:
            async with trio.open_nursery() as nursery:
                print("client: starting services...")
                self._start_all_services()

                print("client: spawning _sender...")
                nursery.start_soon(self._sender, client_stream)

                print("client: spawning _receiver...")
                nursery.start_soon(self._receiver, client_stream)

    @staticmethod
    def build_tui_message(message: str) -> TUIMessage:
        tui_msg = TUIMessage()
        tui_msg.text = message
        # print(f'Built TUI message: {tui_msg}')
        return tui_msg

    def _build_client_info(self) -> bytes:
        client_info = ClientInfo()
        client_info.username = self.username
        return client_info.SerializeToString()

    def build_aio_message(self, base_message: Message) -> AIOMessage:
        aio_msg = AIOMessage()
        aio_msg.message_name = base_message.DESCRIPTOR.name
        aio_msg.message = base_message.SerializeToString()
        aio_msg.client_info.ParseFromString(self._build_client_info())
        # print(f'Built AIO message: {aio_msg}')
        return self._encrypt(aio_msg)

    def parse_aio_message(self, data: bytes) -> AIOMessage:
        """ Parse a received AIOMessage, _decrypt and return results """
        aio_message = AIOMessage()
        aio_message.ParseFromString(data)
        return self._decrypt(aio_message)

    def _decrypt(self, aio_msg: AIOMessage) -> AIOMessage:
        """ Decrypt contents of AIOMessage if necessary """
        # TODO: This...
        return aio_msg

    def _encrypt(self, aio_msg: AIOMessage) -> AIOMessage:
        """ Encrypt contents of AIOMessage if possible """
        # TODO: this...
        return aio_msg

    def cleanup(self):
        """ Client graceful cleanup and terminate """
        # TODO: this...
        pass


if __name__ == '__main__':
    raise not NotImplementedError

