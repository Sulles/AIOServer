"""
All Event Objects
"""


class Event:
    def __init__(self, name: str):
        self.name = name


class TaskResult(Event):
    def __init__(self, task_name: str, success: bool):
        self.task_name = task_name
        self.success = success
        Event.__init__(self, 'TaskEvent')


class ConnectionRx(Event):
    def __init__(self, uuid: int, data: bytes):
        self.uuid = uuid
        self.data = data
        Event.__init__(self, 'ConnectionRx')


class ServerEvent(Event):
    def __init__(self, event_type: str):
        self.event_type = event_type
        Event.__init__(self, 'ServerEvent')
