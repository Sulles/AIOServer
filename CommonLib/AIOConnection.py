"""
AIO Connection Object
"""

import logging

from uuid import UUID
from CommonLib.Events import Event, ConnectionRx
from asyncio import StreamReader, StreamWriter


logger = logging.getLogger(__name__)


class AIOConnection:
    def __init__(self, uuid: UUID, rx: StreamReader, tx: StreamWriter):
        """
        :param uuid:
        :param rx:
        :param tx:
        """
        logger.info(f'=== Got new connection! ===')
        self._uuid = uuid
        self._rx = rx
        self._tx = tx

    async def read(self) -> Event:
        data = await self._rx.read()
        print(f'READ DATA! {data.decode("utf-8")}')
        return ConnectionRx(uuid=self._uuid.int, data=data)

    def write(self, data: bytes):
        self._tx.write(data)
        print(f'Sent data: {data.decode("utf-8")}')
