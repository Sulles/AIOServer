"""
All Event Objects
"""


class Event:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class TextEvent(Event):
    def __init__(self, text: str):
        self.text = text
        Event.__init__(self, 'TextEvent')

    def __str__(self):
        return str(self.__dict__)


class TaskResult(Event):
    def __init__(self, task_name: str, success: bool):
        self.task_name = task_name
        self.success = success
        Event.__init__(self, 'TaskEvent')

    def __str__(self):
        return str(self.__dict__)


class ConnectionRx(Event):
    def __init__(self, uuid: int, data: bytes):
        self.uuid = uuid
        self.data = data
        Event.__init__(self, 'ConnectionRx')

    def __str__(self):
        return str(self.__dict__)


class ServerEvent(Event):
    def __init__(self, event_type: str):
        self.event_type = event_type
        Event.__init__(self, 'ServerEvent')

    def __str__(self):
        return str(self.__dict__)
