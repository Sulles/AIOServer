"""
TUI Service - default Text User Interface endpoint
"""
import trio.lowlevel

from CommonLib.proto.TUIMessage_pb2 import TUIMessage


class TUIService:

    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        register_service('TUIMessage', self._handle_tui_message)

    @staticmethod  # TODO: Finish this...
    async def _handle_tui_message(message: TUIMessage, *args, **kwargs):  # response_callback: trio.lowlevel.wait_writable):
        """ Main entry-way for all TUIMessages """
        tui_message = TUIMessage()
        tui_message.ParseFromString(message)
        print(f'TUIService received TUIMessage: {tui_message}')
