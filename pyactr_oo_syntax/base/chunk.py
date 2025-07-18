"""
Extension of pyactr Chunk class to enable conversion to string and keyword unpacking (**).
"""

from pyactr import ACTRModel, chunkstring
from pyactr.chunks import Chunk

class AdvChunk(Chunk):
    def __init__(self, isa:str, **kwargs):
        super().__init__(typename=isa, **kwargs)

    def __str__(self):
        values = '\n'.join([' '.join((key, str(item))) for key, item in self._asdict().items() if item != None])
        string_representation = f"""isa {self.typename}{'\n'+values if values else ''}"""
        return string_representation
    
    def __getitem__(self, key:str):
        return self.typename if key == 'isa' else (self._asdict().get(key, ''))

    def keys(self) -> list[str]:
        keys = ['isa']
        keys.extend(self._asdict().keys())
        return keys
    
    def add_to_decmem(self, model:ACTRModel, time:int=0):
        cstring = chunkstring(string=str(self))
        model.decmem.add(element=cstring, time=time)
        return cstring
