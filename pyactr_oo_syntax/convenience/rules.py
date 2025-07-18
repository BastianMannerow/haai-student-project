"""
Some predefined rules for convenient use.
"""

from typing import Callable

from pyactr_oo_syntax.base.chunk import AdvChunk
from pyactr_oo_syntax.base.rule_and_production import rule_
from pyactr_oo_syntax.helpers.data_types import Buffer, BufferQuery, RuleType

from pyactr_oo_syntax.convenience.chunks import SimpleGoalChunk, ManualChunk


## Basic Rules ##

class request_(rule_):
    def __init__(self, buffer_name:Buffer|Callable[[str|None],str], imaginal_buffer_name:str|None=None, isa:str|None=None, **chunk_content):
        super().__init__(rule_type=RuleType.REQUEST, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=isa, **chunk_content) 

    @classmethod
    def from_chunk(cls, chunk:AdvChunk, buffer_name:Buffer, imaginal_buffer_name:str|None=None):
        return cls(buffer=buffer_name, imaginal_buffer_name=imaginal_buffer_name, **chunk)


class subsumption_(rule_):
    def __init__(self, buffer_name:Buffer|Callable[[str|None],str], imaginal_buffer_name:str|None=None, isa:str|None=None, **chunk_content):
        super().__init__(rule_type=RuleType.SUBSUMPTION, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=isa, **chunk_content) 

    @classmethod
    def from_chunk(cls, chunk:AdvChunk, buffer_name:Buffer, imaginal_buffer_name:str|None=None):
        return cls(buffer=buffer_name, imaginal_buffer_name=imaginal_buffer_name, **chunk)


class query_(rule_):
    def __init__(self, buffer_name:Buffer|Callable[[str|None],str], imaginal_buffer_name:str|None=None, status:BufferQuery|None=None):
        if status:
            super().__init__(rule_type=RuleType.QUERY, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, **(status.value)) 
        else:
            super().__init__(rule_type=RuleType.QUERY, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name) 

    @classmethod
    def from_chunk(cls, chunk:AdvChunk, buffer_name:Buffer, imaginal_buffer_name:str|None=None):
        return NotImplemented


class flush_(rule_):
    def __init__(self, buffer_name:Buffer|Callable[[str|None],str], imaginal_buffer_name:str|None=None, isa:str|None=None, **chunk_content):
        super().__init__(rule_type=RuleType.FLUSH, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=isa, **chunk_content) 

    @classmethod
    def from_chunk(cls, chunk:AdvChunk, buffer_name:Buffer, imaginal_buffer_name:str|None=None):
        return cls(buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, **chunk)



## Special Rules ##

class is_simple_goal_(rule_):
    def __init__(self, phase:str, **_):
        super().__init__(rule_type=RuleType.SUBSUMPTION, buffer_name=Buffer.GOAL, isa='goal', phase=phase)

    @classmethod
    def from_chunk(cls, chunk:SimpleGoalChunk):
        return cls(**chunk)
    

class is_retrieved_(rule_):
    def __init__(self, isa:str|None=None, **content_to_compare):
        super().__init__(rule_type=RuleType.SUBSUMPTION, buffer_name=Buffer.RETRIEVAL, isa=isa, **content_to_compare)

    @classmethod
    def from_chunk(cls, chunk:AdvChunk):
        return cls(**chunk)


class retrieve_(rule_):
    def __init__(self, isa:str|None=None, **content_to_retrieve):
        super().__init__(rule_type=RuleType.REQUEST, buffer_name=Buffer.RETRIEVAL, isa=isa, **content_to_retrieve)

    @classmethod
    def from_chunk(cls, chunk:AdvChunk):
        return cls(**chunk)


class press_key_(rule_):
    def __init__(self, key:str, **_):
        super().__init__(rule_type=RuleType.REQUEST, buffer_name=Buffer.MANUAL, isa='_manual', cmd='press_key', key=key)

    @classmethod
    def from_chunk(cls, chunk:ManualChunk):
        return cls(**chunk)
    


