"""
Server Chat Bot Service
"""

from datetime import datetime

import trio.lowlevel

from CommonLib.proto.ChatRoomMessage_pb2 import ChatRoomMessage
from Server.util import ServiceRequestEvent

MAX_HISTORY_LENGTH = 10


class ChatRoomService:
    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        self._callbacks: list[trio.lowlevel.wait_writable] = list()
        register_service('ChatRoomMessage', self._handle_chat_bot_message_event)

    async def _broadcast_latest_message(self, message: ChatRoomMessage):
        """ Try to send message to all callbacks """
        print(f'ChatBotService broadcasting message: {message}')
        inactive_callbacks = list()
        for callback in self._callbacks:
            try:
                await callback(message)
            except Exception as e:
                print(f'ChatBotService failed to send message due to error: {e}')
                inactive_callbacks.append(callback)
        for callback in inactive_callbacks:
            self._callbacks.remove(callback)

    async def _broadcast_new_user(self, new_user: str):
        """ Broadcast new user to everyone connected """
        print(f'Broadcasting new user: {new_user}')
        new_user_msg = ChatRoomMessage()
        new_user_msg.author = new_user
        new_user_msg.message = f'{new_user} has connected!'
        setattr(new_user_msg, 'timestamp', datetime.timestamp(datetime.now()))
        await self._broadcast_latest_message(new_user_msg)

    def _save_new_callback(self, callback: trio.lowlevel.wait_writable):
        """ Try to send entire history to new connection """
        print('Saving new callback, sending notification to all users')
        self._callbacks.append(callback)

    async def _handle_chat_bot_message_event(self, event: ServiceRequestEvent):
        """ Callback for every client message """
        chat_bot_message = ChatRoomMessage()
        chat_bot_message.ParseFromString(event.message)
        setattr(chat_bot_message, 'timestamp', datetime.timestamp(datetime.now()))
        print('Entering chat bot message event handler')
        print(f'Is callback known? {event.response_callback in self._callbacks}')
        print(f'Chat bot message received: {event.message}')
        if chat_bot_message.message == '---Start---':
            # print('Entering START')
            if event.response_callback not in self._callbacks:
                self._save_new_callback(event.response_callback)
            await self._broadcast_new_user(chat_bot_message.author)
        elif chat_bot_message.message == '---Stop---':
            print('>>> Entering STOP')
            # Remove from callback
            self._callbacks.remove(event.response_callback)
        else:
            # print('Entering NOMINAL')
            await self._broadcast_latest_message(chat_bot_message)
