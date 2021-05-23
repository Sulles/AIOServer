"""
Server Util
"""

import trio.lowlevel
from google.protobuf.message import Message


class ServiceRequestEvent:
    def __init__(self, requester_uuid: int, service_name: str, message: Message,
                 response_callback: trio.lowlevel.wait_writable):
        """
        Service Request Events are events AIOConnections send to ServerEventProcessor
        :param requester_uuid: Int of originator
        :param service_name: Name of ServiceMessage
        :param message: ServiceMessage used to communicate to specific service
        :param response_callback: Awaitable callback for sending a response
        """
        self.requester_uuid: int = requester_uuid
        self.service_name: str = service_name
        self.message: Message = message
        self.response_callback: trio.lowlevel.wait_writable = response_callback

    def __str__(self):
        return f'Originator: {self.requester_uuid}\n' \
               f'Service Name: {self.service_name}\n' \
               f'Service Message: {self.message}'
