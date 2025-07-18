"""
Enum implementing methods to get the previous or next element of a certain element (useful, e.g., for goal phase sequences).
"""

from enum import Enum

class Sequence(Enum):
    def next(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            index = 0
            # raise StopIteration('end of enumeration reached')
        return members[index]

    def prev(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) - 1
        if index < 0:
            index = len(members) - 1
            #  raise StopIteration('end of enumeration reached')
        return members[index]