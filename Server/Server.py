"""
Server Object
"""

import asyncio
import logging

from asyncio import StreamReader, StreamWriter
from asyncio.queues import Queue
from CommonLib.AIOConnection import AIOConnection
from CommonLib.Events import *
from uuid import uuid1


HOST = '127.0.0.1'
PORT = 8888
logger = logging.getLogger(__name__)


class Server:
    def __init__(self, connection_event_queue: Queue = None):
        """
        Server member variables
        """
        self._connections: dict[int: AIOConnection] = list()
        self._is_running = True
        self._tasks: list[asyncio.Task] = list()
        self._server_event_loop = Queue()

        if connection_event_queue is not None:
            self._add_to_connection_queue = connection_event_queue.put
        else:
            self._add_to_connection_queue = logger.info

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def add_to_event_queue(self, event) -> None:
        await self._server_event_loop.put(event)

    async def register_new_connection(self, rx: StreamReader, tx: StreamWriter):
        uuid = uuid1()
        self._connections[uuid.int] = AIOConnection(uuid, rx, tx)
        self._tasks.append(self._connections[-1].read())

    def process_result(self, result: TaskResult):
        raise NotImplementedError

    async def run(self):
        """
        Main Server run method
        :return:
        """
        server = await asyncio.start_server(self.register_new_connection, HOST, PORT)
        logger.info(f'Started server on: {server.sockets[0].getsockname()}')

        task = asyncio.create_task(server.serve_forever())
        task.set_name('server_listener')
        self._tasks.append(task)

        while self.is_running:
            for task in self._tasks:
                if task.done():
                    if task.cancelled():
                        logger.warning(f'Task "{task.get_name()}" was cancelled!')
                    else:
                        result = task.result()

    def cleanup(self):
        """
        Server graceful cleanup and terminate
        :return:
        """
        raise NotImplementedError


if __name__ == '__main__':
    my_server = Server()
    try:
        asyncio.run(my_server.run())

    except KeyboardInterrupt:
        logger.warning('--- Keyboard Interrupt Detected ---')

    finally:
        my_server.cleanup()
