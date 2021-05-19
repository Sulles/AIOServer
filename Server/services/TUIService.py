"""
TUI Service - default Text User Interface endpoint
"""

from CommonLib.proto.TUIMessage_pb2 import TUIMessage
from Server.util import ServiceRequestEvent


class TUIService:

    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        register_service('TUIMessage', self._handle_tui_message)

    @staticmethod
    async def _handle_tui_message(event: ServiceRequestEvent):
        """ Main entry-way for all TUIMessages """
        tui_message = TUIMessage()
        tui_message.ParseFromString(event.message)
        print(f'TUIService received TUIMessage: {tui_message}')
