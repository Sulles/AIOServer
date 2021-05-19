"""
Client Objects
"""

import os
import sys
from copy import copy
from enum import IntEnum

import trio
from google.protobuf.message import Message

from CommonLib.proto.AIOMessage_pb2 import AIOMessage
from CommonLib.proto.TUIMessage_pb2 import TUIMessage
from CommonLib.proto.ChatBotMessage_pb2 import ChatBotMessage
from .KBHit import KBHit

HOST = '127.0.0.1'
PORT = 8888
TUI_HISTORY_LENGTH = 10


class Client:
    """
    Client connection to AIOServer
    """
    tx_send_server_channel: trio.abc.SendChannel[AIOMessage]
    rx_send_server_channel: trio.abc.ReceiveChannel[AIOMessage]

    def __init__(self):
        self._is_alive = True
        self.username = ''  # TODO: implement login with security
        self._service_map: dict[str, classmethod] = dict()

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
        sys.exit()

    async def run(self):
        print(f"client: connecting to {HOST}:{PORT}")
        client_stream = await trio.open_tcp_stream(HOST, PORT)
        self.tx_send_server_channel, self.rx_send_server_channel = trio.open_memory_channel(0)
        async with client_stream:
            async with trio.open_nursery() as nursery:
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

    def build_aio_message(self, base_message: Message) -> AIOMessage:
        aio_msg = AIOMessage()
        aio_msg.message_name = base_message.DESCRIPTOR.name
        aio_msg.message = base_message.SerializeToString()
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


class TuiState(IntEnum):
    TUI = 0
    ChatBot = 1


class TuiEventType(IntEnum):
    UserEvent = 0
    ServerEvent = 1


class TUIEvent:
    def __init__(self, event_type: TuiEventType, data: str):
        self.event_type = event_type
        self.data = data

    def __str__(self):
        return f'Event Type: {self.event_type}\n' \
               f'Data: {self.data}'


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
        self._state = TuiState.TUI
        self._commands = {'help': self._get_help,
                          'set state tui': self._set_state_tui,
                          'set state chatbot': self._set_state_chatbot}
        Client.__init__(self)

    def _get_help(self) -> str:
        return f'Available TUI Commands: {list(self._commands.keys())}'

    def _set_state_tui(self) -> None:
        """ Set TUI object state to TUI """
        self._state = TuiState.TUI

    def _set_state_chatbot(self) -> None:
        """ Set TUI object state to ChatBot """
        self._state = TuiState.ChatBot

    def _build_state_message(self, text: str) -> Message:
        """ Build state specific message """
        if self._state == TuiState.TUI:
            return self.build_tui_message(text)
        elif self._state == TuiState.ChatBot:
            return self._build_chat_bot_message(text)

    def _build_chat_bot_message(self, message: str) -> ChatBotMessage:
        """ Build ChatBotMessage """
        chat_bot_message = ChatBotMessage()
        chat_bot_message.author = self.username
        chat_bot_message.message = message
        return chat_bot_message

    async def _tui_event_processor(self) -> None:
        """ TUI event processor """
        print('Starting tui event processor')
        async for tui_event in self.rx_tui_event:
            # print(f'TUI event processor got event!: {tui_event}')
            if tui_event.event_type == TuiEventType.UserEvent:
                # Windows return is '\r', unix return is '\n'
                if tui_event.data == ('\r' if os.name == 'nt' else '\n'):
                    await self._commit_user_input()
                else:
                    if tui_event.data == '\x08':    # backspace
                        self._user_input = self._user_input[:-1]
                    else:
                        self._user_input += tui_event.data
            elif tui_event.event_type == TuiEventType.ServerEvent:
                self._add_to_history(f'TUI event processor got server event! '
                                     f'Event data: {tui_event.data}')
                self._add_to_history(self._parse_server_event_by_state(tui_event.data))

    def _parse_server_event_by_state(self, aio_message: AIOMessage) -> str:
        return aio_message

    async def _commit_user_input(self) -> None:
        """ Commit user input to history and send to Server """
        if self._user_input in self._commands.keys():
            self._history.append(self._commands[self._user_input]())
        elif len(self._user_input) > 0:
            await self.tx_send_server_channel.send(
                self.build_aio_message(
                    self._build_state_message(self._user_input)))
            # Only add message to user history if not using the chat bot
            if self._state != TuiState.ChatBot:
                self._add_to_history(self._user_input)
        self._user_input = ''

    def _add_to_history(self, text: str) -> None:
        """ Add text to TUI history """
        # print(f'Adding {text} to history')
        if len(self._history) >= TUI_HISTORY_LENGTH:
            self._history.pop(0)
        self._history.append(text)

    async def _receiver(self, client_stream) -> None:
        """ Override Client._receiver """
        print("TUI _receiver: started!")
        async for data in client_stream:
            # print(f"TUI _receiver: got data {data!r}")
            await self.tx_tui_event.send(
                TUIEvent(TuiEventType.ServerEvent, data=self.parse_aio_message(data)))
        print("TUI _receiver: connection closed")
        sys.exit()

    async def run(self) -> None:
        print('Starting TUI...')

        # Create event channels
        self.tx_tui_event, self.rx_tui_event = trio.open_memory_channel(0)
        self.tx_send_server_channel, self.rx_send_server_channel = trio.open_memory_channel(0)

        # Create client stream to server
        client_stream = await trio.open_tcp_stream(HOST, PORT)

        async with trio.open_nursery() as nursery:
            print("tui: spawning _sender...")
            nursery.start_soon(self._sender, client_stream)

            print("tui: spawning _receiver...")
            nursery.start_soon(self._receiver, client_stream)

            print("tui: spawning event processor...")
            nursery.start_soon(self._tui_event_processor)

            print('tui: spawning _getch...')
            nursery.start_soon(self._getch)

            print('tui: spawning _tui_interface...')
            nursery.start_soon(self._tui_interface)

    async def _getch(self) -> None:
        """ Get character that a user has put in """
        await trio.sleep(0.2)   # don't be the first thing to start
        while True:
            with trio.move_on_after(0.1):
                # Put self at end of event loop
                for _ in range(5):
                    await trio.sleep(0.001)
                data = self._kbhit.getch()
                if data in [_.decode('utf-8') for _ in [b'\x03', b'\x1a']]:
                    sys.exit()
                await self.tx_tui_event.send(
                    TUIEvent(TuiEventType.UserEvent, data=data))

    async def _tui_interface(self) -> None:
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

            await trio.sleep(0.001)


if __name__ == '__main__':
    tui = TUI()

    try:
        trio.run(tui.run)

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    finally:
        tui.cleanup()
