"""
TUI Class
"""

import sys
import os
import datetime

from copy import copy
from enum import IntEnum
from queue import Queue, Empty
from threading import Thread

from CommonLib.proto.ChatRoomMessage_pb2 import ChatRoomMessage

from .Client import *
from .KBHit import KBHit


class TuiState(IntEnum):
    TUI = 0
    ChatRoom = 1


class TuiEventType(IntEnum):
    Getch = 0
    ServerMessage = 1


class TUIEvent:
    def __init__(self, event_type: TuiEventType, data: str):
        self.event_type = event_type
        self.data = data

    def __str__(self):
        return f'Event Type: {self.event_type}\n' \
               f'Data: {self.data}'


def enqueue_getch(input_queue: Queue, kbhit: KBHit):
    """ Enqueue getch data from KBHit object """
    while True:
        try:
            new_input = kbhit.getch()
            if new_input == '\x1b':
                raise ClientTerminationEvent
            elif new_input is not None:
                input_queue.put(new_input)
        except UnicodeDecodeError:
            break
    print('CRITICAL ERROR: Getch no longer functional!')


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
        self._getch_queue = Queue()
        self._getch_thread = Thread(target=enqueue_getch, args=(self._getch_queue, self._kbhit,))
        self._history: list = ['']
        self._user_input: str = ''
        self._state = TuiState.TUI
        self._commands = {'help': self._get_help,
                          'set state tui': self._set_state_tui,
                          'set state chatroom': self._set_state_chatroom}
        Client.__init__(self)

    async def _get_help(self) -> str:
        return f'Available TUI Commands: {list(self._commands.keys())}'

    async def _set_state_tui(self) -> None:
        """ Set TUI object state to TUI """
        self._state = TuiState.TUI
        await self.tx_send_server_channel.send(
            self.build_aio_message(
                self._build_chat_bot_message('---Stop---')))

    async def _set_state_chatroom(self) -> None:
        """ Set TUI object state to ChatRoom """
        self._state = TuiState.ChatRoom
        await self.tx_send_server_channel.send(
            self.build_aio_message(
                self._build_chat_bot_message('---Start---')))

    def _build_state_message(self, text: str) -> Message:
        """ Build state specific message """
        if self._state == TuiState.TUI:
            return self.build_tui_message(text)
        elif self._state == TuiState.ChatRoom:
            return self._build_chat_bot_message(text)

    def _build_chat_bot_message(self, message: str) -> ChatRoomMessage:
        """ Build ChatRoomMessage """
        chat_bot_message = ChatRoomMessage()
        chat_bot_message.author = self.username
        chat_bot_message.message = message
        return chat_bot_message

    async def _tui_event_processor(self) -> None:
        """ TUI event processor """
        print('Starting tui event processor')
        async for tui_event in self.rx_tui_event:
            # If event was generated by a getch
            if tui_event.event_type == TuiEventType.Getch:
                # Windows return is '\r', unix return is '\n'
                if tui_event.data == ('\r' if os.name == 'nt' else '\n'):
                    # Only commit user input on "return/enter"
                    await self._commit_user_input()
                else:
                    # Otherwise just append data to the user input
                    if tui_event.data == ('\x08' if os.name == 'nt' else '\x7f'):    # backspace
                        self._user_input = self._user_input[:-1]
                    else:
                        self._user_input += tui_event.data
            # If event was generated by a server message
            elif tui_event.event_type == TuiEventType.ServerMessage:
                # self._add_to_history(f'TUI event processor got server event! '
                #                      f'Event data: {tui_event.data}')
                self._add_to_history(self._parse_server_message_to_string(tui_event.data))

    def _parse_server_message_to_string(self, aio_message: AIOMessage) -> str:
        """ Parse an AIOMessage sent by the AIOServer and return string data """
        if self._state == TuiState.ChatRoom:
            chat_bot_msg = ChatRoomMessage()
            if aio_message.message_name != chat_bot_msg.DESCRIPTOR.name:
                print(f'Expected "ChatRoomMessage", received: "{aio_message.message_name}"')
            else:
                chat_bot_msg.ParseFromString(aio_message.message)
                timestamp = datetime.datetime.fromtimestamp(chat_bot_msg.timestamp)
                return f'[{timestamp.strftime("%a - %H:%M:%S")}] {chat_bot_msg.author}: ' \
                       f'{chat_bot_msg.message}'
        else:
            return f'Received message "{aio_message.message_name}" with data:\n' \
                   f'{aio_message.message}'

    async def _commit_user_input(self) -> None:
        """ Commit user input to history and send to Server """
        if self._user_input in self._commands.keys():
            self._history.append(
                await self._commands[self._user_input]())
        elif len(self._user_input) > 0:
            await self.tx_send_server_channel.send(
                self.build_aio_message(
                    self._build_state_message(self._user_input)))
            # Only add message to user history if not using the chat bot
            if self._state != TuiState.ChatRoom:
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
                TUIEvent(TuiEventType.ServerMessage, data=self.parse_aio_message(data)))
        print("TUI _receiver: connection closed")
        raise ClientTerminationEvent

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
            self._getch_thread.start()
            nursery.start_soon(self._getch)

            print('tui: spawning _tui_interface...')
            nursery.start_soon(self._tui_interface)

    async def _getch(self) -> None:
        """ Get character that a user has put in """
        await trio.sleep(0.2)   # don't be the first thing to start
        while True:
            try:
                data = self._getch_queue.get(timeout=0.01)
                if data in [_.decode('utf-8') for _ in [b'\x03', b'\x1a']]:
                    sys.exit()
                await self.tx_tui_event.send(
                    TUIEvent(TuiEventType.Getch, data=data))
                await trio.sleep(0)     # Checkpoint for other trio events
            except Empty:
                await trio.sleep(0.01)

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

    def cleanup(self):
        """ Add Getch cleanup to base Client cleanup """

        print('Press "Delete" to exit...')
        self._getch_thread.join()

        # Call base client cleanup
        Client.cleanup(self)


if __name__ == '__main__':
    tui = TUI()

    try:
        trio.run(tui.run)

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    finally:
        tui.cleanup()
