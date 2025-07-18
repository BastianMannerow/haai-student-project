"""
Definitions for ACT-R elements that can only take certain values. 
"""

from enum import Enum
from typing import Callable


class RuleType(Enum):
    REQUEST = '+'
    SUBSUMPTION = '='
    QUERY = '?'
    FLUSH = '~'


class Buffer(Enum):
    GOAL = 'g'
    RETRIEVAL = 'retrieval'
    VISUAL = 'visual'
    VISUAL_LOCATION = 'visual_location'
    MANUAL = 'manual'
    IMAGINAL:Callable[[str|None],str] = lambda x: f"imaginal{'_' + x if x else ''}"


class BufferQuery(Enum):
        pass

class BufferStatus():
    class GoalBufferStatus(BufferQuery):    
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    class RetrievalBufferStatus(BufferQuery):
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    class VisualBufferStatus(BufferQuery):
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    class VisuallocationBufferStatus(BufferQuery):
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    class ManualBufferStatus(BufferQuery):
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    class ImaginalBufferStatus(BufferQuery):
        FULL = {'buffer':'full'}
        EMPTY = {'buffer':'empty'}
        FAILURE = {'buffer':'failure'}
        REQUESTED = {'buffer':'requested'}
        UNREQUESTED = {'buffer':'unrequested'}
        BUSY = {'state':'busy'}
        FREE = {'state':'free'}
        ERROR = {'state':'error'}
        NOERROR = {'error':'nil'}

    GOAL = GoalBufferStatus
    RETRIEVAL = RetrievalBufferStatus
    VISUAL = VisualBufferStatus
    VISUAL_LOCATION = VisuallocationBufferStatus
    MANUAL = ManualBufferStatus
    IMAGINAL = ImaginalBufferStatus

class BufferExtraTest():
    class VisuallocationExtraTest(BufferQuery):
        ATTENDED = {'attended':True}
        NOT_ATTENDED = {'attended':False}


class static_chunk_slot:
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, _, owner):
        return self.getter(owner)