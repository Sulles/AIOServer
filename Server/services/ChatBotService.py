"""
Server Chat Bot Service
"""

from datetime import datetime

import trio.lowlevel

from CommonLib.proto.ChatBotMessage_pb2 import ChatBotMessage
from Server.util import ServiceRequestEvent

MAX_HISTORY_LENGTH = 10


class ChatBotService:
    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        self._history: list[ChatBotMessage] = list()
        self._callbacks: list[trio.lowlevel.wait_writable] = list()
        register_service('ChatBotMessage', self._handle_chat_bot_message_event)

    def _add_to_history(self, message: ChatBotMessage):
        """ Add ChatBotMessage to ChatBotService history """
        # If more than MAX_HISTORY_LENGTH messages in history, pop first element
        if len(self._history) > MAX_HISTORY_LENGTH:
            self._history.pop(0)
        # Add message to history
        self._history.append(message)

    async def _broadcast_latest_message(self, message: ChatBotMessage):
        """ Try to send message to all callbacks """
        print(f'ChatBotService broadcasting message: {message}')
        for callback in self._callbacks:
            try:
                await callback(message)
            except Exception as e:
                print(f'ChatBotService failed to send message due to error: {e}')
                self._callbacks.remove(callback)

    async def _save_new_callback(self, callback: trio.lowlevel.wait_writable):
        """ Try to send entire history to new connection """
        print(f'Saving new callback, trying to send all messages in history:\n{self._history}')
        for message in self._history:
            try:
                await callback(message)
            except Exception as e:
                print(f'ChatBotService failed to send ChatBot history due to error: {e}')
        self._callbacks.append(callback)

    async def _handle_chat_bot_message_event(self, event: ServiceRequestEvent):
        """ Callback for every client message """
        chat_bot_message = ChatBotMessage()
        chat_bot_message.ParseFromString(event.message)
        setattr(chat_bot_message, 'timestamp', datetime.timestamp(datetime.now()))
        self._add_to_history(chat_bot_message)
        print('Entering chat bot message event handler')
        print(f'Is callback known? {event.response_callback in self._callbacks}')
        print(f'Chat bot message received: {event.message}')
        if event.response_callback not in self._callbacks and b'---Start---' in event.message:
            print('Entering START')
            await self._save_new_callback(event.response_callback)
        elif event.message == '---Stop---':
            print('Entering STOP')
            # Remove from callback
            del self._callbacks[event.response_callback]
        else:
            print('Entering OTHER')
            await self._broadcast_latest_message(chat_bot_message)
