"""
Server Util
"""

import trio.lowlevel
from google.protobuf.message import Message


class ServiceRequestEvent:
    def __init__(self, service_name: str, service_message: Message,
                 response_callback: trio.lowlevel.wait_writable):
        """
        Service Request Events are events AIOConnections send to ServerEventProcessor
        :param service_name: Name of ServiceMessage
        :param service_message: ServiceMessage used to communicate to specific service
        :param response_callback: Awaitable callback for sending a response
        """
        self.service_name = service_name
        self.service_message = service_message
        self.response_callback = response_callback

    def __str__(self):
        return f'Service Name: {self.service_name}\n' \
               f'Service Message: {self.service_message}'
