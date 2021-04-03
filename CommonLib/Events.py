"""
All Event Objects
"""

from dataclasses import dataclass


class Event(dataclass):
    name: str


class TaskResult(Event):
    super().name = 'TaskResult'
    task_name: str
    success: bool


class ConnectionRx(Event):
    super().name = 'ConnectionRx'
    uuid: int
    data: bytes


class ServerEvent(Event):
    super().name = 'ServerEvent'
    event_type: str
