from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class WorkerInfo(_message.Message):
    __slots__ = ("workerId", "gpuCount", "gpuType", "workerName")
    WORKERID_FIELD_NUMBER: _ClassVar[int]
    GPUCOUNT_FIELD_NUMBER: _ClassVar[int]
    GPUTYPE_FIELD_NUMBER: _ClassVar[int]
    WORKERNAME_FIELD_NUMBER: _ClassVar[int]
    workerId: str
    gpuCount: int
    gpuType: str
    workerName: str
    def __init__(self, workerId: _Optional[str] = ..., gpuCount: _Optional[int] = ..., gpuType: _Optional[str] = ..., workerName: _Optional[str] = ...) -> None: ...

class Ack(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class WorkRequest(_message.Message):
    __slots__ = ("task", "taskid")
    TASK_FIELD_NUMBER: _ClassVar[int]
    TASKID_FIELD_NUMBER: _ClassVar[int]
    task: str
    taskid: str
    def __init__(self, task: _Optional[str] = ..., taskid: _Optional[str] = ...) -> None: ...

class WorkResponse(_message.Message):
    __slots__ = ("text", "taskid")
    TEXT_FIELD_NUMBER: _ClassVar[int]
    TASKID_FIELD_NUMBER: _ClassVar[int]
    text: str
    taskid: str
    def __init__(self, text: _Optional[str] = ..., taskid: _Optional[str] = ...) -> None: ...

class WorkResponseAck(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
