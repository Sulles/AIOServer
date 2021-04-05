"""
Server object
"""

import asyncio

from asyncio import StreamReader, StreamWriter
from asyncio.queues import Queue
from CommonLib.AIOConnection import AIOConnection
from CommonLib.Events import *
from uuid import uuid1


HOST = '127.0.0.1'
PORT = 8888


class Server:
    def __init__(self, loop: asyncio.AbstractEventLoop, connection_event_queue: Queue = None):
        """
        Server member variables
        """
        # Save Server event loop
        self._loop = loop

        # Save all tasks
        self._tasks: list[asyncio.Task] = list()

        # Define all member variables
        self._connections: dict[str: AIOConnection] = dict()
        self._is_running = True
        self._server_event_queue = Queue()

        if connection_event_queue is not None:
            self._add_to_connection_queue = connection_event_queue.put
        else:
            self._add_to_connection_queue = print

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def add_to_event_queue(self, event) -> None:
        await self._server_event_queue.put(event)

    async def register_new_connection(self, rx: StreamReader, tx: StreamWriter):
        print(f'=== Entering "register_new_connection"! ===')
        uuid = uuid1()
        self._connections[uuid.hex] = AIOConnection(uuid, rx, tx)
        # Add task to Server event loop
        task = self._loop.create_task(
            self._connections[uuid.hex].read(),
            name='register_new_connection')
        self._tasks.append(task)
        print(f'self._tasks: {self._tasks}')

    def process_result(self, result: TaskResult):
        raise NotImplementedError

    async def run(self):
        """
        Main Server run method
        :return:
        """
        server = await asyncio.start_server(self.register_new_connection, HOST, PORT, loop=self._loop)
        print(f'Started server on: {server.sockets[0].getsockname()}')
        self._loop.create_task(
            server.serve_forever(),
            name='server_listener')

        while self.is_running:
            print('.')
            finished_tasks = [task for task in self._tasks if task.done()]
            if len(finished_tasks) != 0:
                [print(f'Got finished task: {task}') for task in finished_tasks]

            self._tasks = [task for task in self._tasks if not task.done()]
            # [print(f'Waiting on task: {task}') for task in self._tasks]
            # for future in asyncio.as_completed(self._tasks):
            #     result = await future
            #     print(f'Got future result?! {result}')

            await asyncio.sleep(0.1)

    def cleanup(self):
        """
        Server graceful cleanup and terminate
        :return:
        """
        # TODO: this...
        pass


if __name__ == '__main__':
    server_loop = asyncio.new_event_loop()
    my_server = Server(server_loop)

    try:
        server_loop.set_debug(True)
        server_loop.run_until_complete(my_server.run())

    except KeyboardInterrupt:
        print('\n--- Keyboard Interrupt Detected ---\n')

    finally:
        my_server.cleanup()
