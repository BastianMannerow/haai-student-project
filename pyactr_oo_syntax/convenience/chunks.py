"""
Some predefined chunks for convenient use.
"""

from pyactr_oo_syntax.base.chunk import AdvChunk
from pyactr_oo_syntax.helpers.data_types import static_chunk_slot

class SimpleGoalChunk(AdvChunk):
    @static_chunk_slot
    def isa(cls) -> str:
        return 'goal'

    def __init__(self, phase:str):
        super().__init__(isa=SimpleGoalChunk.isa, phase=phase)


class VisuallocationChunk(AdvChunk):
    @static_chunk_slot
    def isa(cls) -> str:
        return '_visuallocation'

    def __init__(self, screen_x:str|None=None, screen_y:str|None=None, attended:str|None=None, **kwargs):
        new_kwargs:dict = kwargs
        for var_name, var_value in {'screen_x':screen_x, 'screen_y':screen_y, 'attended':attended}.items():
            if var_value:
                new_kwargs[var_name] = var_value
        super().__init__(isa=VisuallocationChunk.isa, **new_kwargs)


class VisualChunk(AdvChunk):
    @static_chunk_slot
    def isa(cls) -> str:
        return '_visual'

    def __init__(self, value:str|None=None, cmd:str|None=None, screen_pos:VisuallocationChunk|None=None, **kwargs):
        new_kwargs:dict = kwargs
        for var_name, var_value in {'value':value, 'cmd':cmd, 'screen_pos':screen_pos}.items():
            if var_value:
                new_kwargs[var_name] = var_value      
        super().__init__(isa=VisualChunk.isa, **new_kwargs)


class ManualChunk(AdvChunk):
    @static_chunk_slot
    def isa(cls) -> str:
        return '_manual'

    def __init__(self, cmd:str|None=None, key:str|None=None, **kwargs):
        new_kwargs:dict = kwargs
        for var_name, var_value in {'cmd':cmd, 'key':key}.items():
            if var_value:
                new_kwargs[var_name] = var_value      
        super().__init__(isa=ManualChunk.isa, **new_kwargs)
