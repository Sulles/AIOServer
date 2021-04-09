import os
import sys
from copy import copy
from enum import IntEnum

import trio
from google.protobuf.message import Message

from CommonLib.proto.AIOMessage_pb2 import AIOMessage
from CommonLib.proto.TextMessage_pb2 import TextMessage
from .KBHit import KBHit

HOST = '127.0.0.1'
PORT = 8888
TUI_HISTORY_LENGTH = 10


class Client:
    """
    Client connection to AIOServer
    """
    tx_send_server_channel: trio.abc.SendChannel
    rx_send_server_channel: trio.abc.ReceiveChannel

    def __init__(self, is_dummy: bool = False):
        self._is_dummy = is_dummy
        self._is_alive = True

    @property
    def is_alive(self):
        return self.is_alive

    async def sender(self, client_stream):
        """ Sender """
        print("sender: started!")
        if not self._is_dummy:
            async for data in self.rx_send_server_channel:
                print(f"sender: sending {data!r}")
                await client_stream.send_all(data)
        else:
            while True:
                data = input('> ')
                await client_stream.send_all(data.encode('utf-8'))
                await trio.sleep(0.1)

    async def receiver(self, client_stream):
        """ Receiver """
        # TODO: Finalize this for use
        print("receiver: started!")
        async for data in client_stream:
            print(f"receiver: got data {data!r}")
        print("receiver: connection closed")
        sys.exit()

    async def run(self):
        print(f"client: connecting to {HOST}:{PORT}")
        client_stream = await trio.open_tcp_stream(HOST, PORT)
        self.tx_send_server_channel, self.rx_send_server_channel = trio.open_memory_channel(0)
        async with client_stream:
            async with trio.open_nursery() as nursery:
                print("client: spawning sender...")
                nursery.start_soon(self.sender, client_stream)

                print("client: spawning receiver...")
                nursery.start_soon(self.receiver, client_stream)

    @staticmethod
    def build_text_message(message: str) -> TextMessage:
        txt_msg = TextMessage()
        txt_msg.text_message = message
        return txt_msg

    def build_aio_message(self, base_message: Message) -> AIOMessage:
        aio_msg = AIOMessage()
        aio_msg.message_name = base_message.DESCRIPTOR.name
        return self.encrypt(aio_msg)

    def encrypt(self, aio_msg: AIOMessage):
        # TODO: this...
        return aio_msg

    def cleanup(self):
        """ Client graceful cleanup and terminate """
        # TODO: this...
        pass


class TuiEventType(IntEnum):
    UserEvent = 0
    ServerEvent = 1


class TUIEvent:
    def __init__(self, event_type: TuiEventType, data: str):
        self.event_type = event_type
        self.data = data

    def __str__(self):
        return str(self.__dict__)


def clear_screen():
    # Clear terminal
    if os.name == 'nt':  # if windows
        os.system('cls')
    else:  # if unix
        os.system('clear')


class TUI(Client):
    """
    Text User Interface (TUI) to AIOServer
    """
    tx_tui_event: trio.abc.SendChannel
    rx_tui_event: trio.abc.ReceiveChannel

    def __init__(self):
        self._kbhit = KBHit()
        self._history: list = ['']
        self._user_input: str = ''
        Client.__init__(self)

    async def tui_event_processor(self):
        """ TUI event processor """
        print('Starting tui event processor')
        async for tui_event in self.rx_tui_event:
            # print(f'TUI event processor got event!: {tui_event}')
            if tui_event.event_type == TuiEventType.UserEvent:
                if tui_event.data == '\r':
                    self.commit_user_input_to_history()
                else:
                    if tui_event.data == '\x08':
                        self._user_input = self._user_input[:-1]
                    else:
                        self._user_input += tui_event.data
            elif tui_event.event_type == TuiEventType.ServerEvent:
                self.add_to_history(tui_event.data)

    def commit_user_input_to_history(self):
        """ Commit user input to history """
        self.add_to_history(self._user_input)
        self._user_input = ''

    def add_to_history(self, text: str):
        """ Add text to TUI history """
        # print(f'Adding {text} to history')
        if len(self._history) >= TUI_HISTORY_LENGTH:
            self._history.pop(0)
        self._history.append(text)

    async def receiver(self, client_stream):
        """ Override Client.receiver """
        print("receiver: started!")
        async for data in client_stream:
            # print(f"receiver: got data {data!r}")
            await self.tx_tui_event.send(
                TUIEvent(TuiEventType.ServerEvent, data=data))
            await trio.sleep(0.01)
        print("receiver: connection closed")
        sys.exit()

    async def run(self):
        print('Starting TUI...')

        # Create event channels
        self.tx_tui_event, self.rx_tui_event = trio.open_memory_channel(0)
        self.tx_send_server_channel, self.rx_send_server_channel = trio.open_memory_channel(0)

        # Create client stream to server
        client_stream = await trio.open_tcp_stream(HOST, PORT)

        async with trio.open_nursery() as nursery:
            print("tui: spawning sender...")
            nursery.start_soon(self.sender, client_stream)

            print("tui: spawning receiver...")
            nursery.start_soon(self.receiver, client_stream)

            print("tui: spawning event processor...")
            nursery.start_soon(self.tui_event_processor)

            print('tui: spawning getch...')
            nursery.start_soon(self.getch)

            print('tui: spawning tui_interface...')
            nursery.start_soon(self.tui_interface)

    async def getch(self):
        """ Get character that a user has put in """
        await trio.sleep(0.2)   # don't be the first thing to start
        while True:
            with trio.move_on_after(1):
                data = self._kbhit.getch()
                if data in [_.decode('utf-8') for _ in [b'\x03', b'\x1a']]:
                    sys.exit()
                await self.tx_tui_event.send(
                    TUIEvent(TuiEventType.UserEvent, data=data))
                await trio.sleep(0.01)

    async def tui_interface(self):
        """ Tui interface """
        # Store previous info so updates are only done on-change
        previous_last_history = self._history[-1]
        previous_user_input = copy(self._user_input)
        default_whitespace_length = 50

        await trio.sleep(0.1)   # wait for everything to spawn and start

        # Build default interface
        clear_screen()
        print('\nWelcome to AIOServer TUI!')
        print('\n-----------------------------------------\n')

        while True:
            # If history or user input has changed
            if self._history[-1] != previous_last_history or \
                    self._user_input != previous_user_input:

                if self._history[-1] != previous_last_history:
                    # Update to latest message
                    previous_last_history = self._history[-1]

                    # Clear terminal
                    clear_screen()

                    # Re-print history
                    [print(_) for _ in self._history]

                    # Add line
                    print('\n-----------------------------------------\n')

                # Update to latest user input
                previous_user_input = copy(self._user_input)

                # Re-write user input
                if len(previous_user_input) > default_whitespace_length:
                    default_whitespace_length = len(previous_user_input) + 10
                elif len(previous_user_input) < 10:
                    default_whitespace_length = 50
                sys.stdout.write('\r' + ''.join([' ' for _ in range(default_whitespace_length)]) +
                                 '\r> ' + self._user_input)

            await trio.sleep(0.003)


if __name__ == '__main__':
    tui = TUI()

    try:
        trio.run(tui.run)

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    finally:
        tui.cleanup()

    # client = Client(is_dummy=True)
    #
    # try:
    #     trio.run(client.run)
    #
    # except KeyboardInterrupt:
    #     print('\n--- Keyboard Interrupt Detected ---\n')
    #
    # finally:
    #     client.cleanup()
