"""
Client Chat Bot Service
"""

from CommonLib.proto.ChatRoomMessage_pb2 import ChatBotMessage


class ChatBotService:
    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        register_service('ChatBotMessage', self._handle_chat_bot_message)

    @staticmethod
    def _handle_chat_bot_message(message: bytes):
        chat_bot_message = ChatBotMessage()
        chat_bot_message.ParseFromString(message)
        return message
