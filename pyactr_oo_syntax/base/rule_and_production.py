"""
Base implementation for rules, rule sequences, productions, and production sequences that support being combined via the operators &, >>, and +.
"""

from __future__ import annotations
from typing import Callable
from copy import copy
from pyactr import ACTRModel

from pyactr_oo_syntax.base.chunk import AdvChunk
from pyactr_oo_syntax.helpers.data_types import RuleType, Buffer


## Foundation Classes: rule_, rule_sequence_, production, production_sequence ##

class rule_():
    def __init__(self, rule_type:RuleType, buffer_name:Buffer|Callable[[str|None],str], imaginal_buffer_name:str|None=None, isa:str|None=None, **chunk_content):
        self.__rule_type:RuleType = rule_type
        self.__buffer:Buffer|str = buffer_name(imaginal_buffer_name) if isinstance(buffer_name, Callable) else buffer_name
        self.__content:AdvChunk|str|None = None
        if rule_type == RuleType.QUERY:
            self.__content = '\n'.join([f"{key} {value}" for key, value in chunk_content.items() if value != None])
        elif isa != None:
            self.__content = AdvChunk(isa, **chunk_content)

    def __str__(self):
        return f"{self.__rule_type.value}{self.__buffer.value if isinstance(self.__buffer, Buffer) else self.__buffer}>{'\n'+str(self.__content) if self.__content else ''}"

    def __and__(self, other:rule_|rule_sequence_) -> rule_sequence_:
        if isinstance(other, rule_):
            return rule_sequence_(rules=[copy(self), copy(other)])
        elif isinstance(other, rule_sequence_):
            return rule_sequence_(rules=[copy(self)]) & other
        else:
            return NotImplemented
        
    def __rshift__(self, other:rule_|rule_sequence_) -> production:
        if isinstance(other, rule_):
            return production(lhs=rule_sequence_(rules=[copy(self)]), rhs=rule_sequence_(rules=[copy(other)]))
        elif isinstance(other, rule_sequence_):
            return production(lhs=rule_sequence_(rules=[copy(self)]), rhs=copy(other))
        else:
            return NotImplemented


class rule_sequence_():
    def __init__(self, rules: list[rule_]):
        self.rules: list[rule_] = rules

    def __str__(self) -> str:
        return '\n'.join(map(str, self.rules))  

    def __and__(self, other:rule_|rule_sequence_) -> rule_sequence_:
        if isinstance(other, rule_):
            new_rules = copy(self.rules)
            new_rules.append(other)
            return rule_sequence_(rules=new_rules)
        elif isinstance(other, rule_sequence_):
            new_rules = copy(self.rules)
            new_rules.extend(other.rules)
            return rule_sequence_(rules=new_rules)
        else:
            return NotImplemented

    def __rshift__(self, other:rule_|rule_sequence_) -> production:
        if isinstance(other, rule_):
            return production(lhs=copy(self), rhs=rule_sequence_(rules=[copy(other)]))
        elif isinstance(other, rule_sequence_):
            return production(lhs=copy(self), rhs=copy(other))
        else:
            return NotImplemented


class production:
    def __init__(self, lhs: rule_sequence_, rhs: rule_sequence_):
        self.__name = None
        self.__lhs: rule_sequence_ = lhs
        self.__rhs: rule_sequence_ = rhs
        self.__utility:int = 0
        self.__reward:float|None = None

    def __str__(self):
        return f"{str(self.__lhs)}\n==>\n{str(self.__rhs)}"
    
    def __and__(self, other:rule_|rule_sequence_) -> production:
        if isinstance(other, rule_):
            return production(lhs=copy(self.__lhs), rhs=self.__rhs & rule_sequence_(rules=[copy(other)]))
        elif isinstance(other, rule_sequence_):
            return production(lhs=copy(self.__lhs), rhs=self.__rhs & other)
        else:
            return NotImplemented

    def __rand__(self, other:rule_|rule_sequence_) -> production:
        if isinstance(other, rule_):
            return production(lhs=rule_sequence_(rules=[copy(other)]) & self.__lhs, rhs=copy(self.__rhs))
        elif isinstance(other, rule_sequence_):
            return production(lhs=other & self.__lhs, rhs=copy(self.__rhs))
        else:
            return NotImplemented
        
    def __rshift__(self, other:object) -> TypeError:
        raise SyntaxError('Productions cannot get another left- or right-hand side. Use & to add more Rules or RuleSequences.')
    
    def __add__(self, other:production|production_sequence) -> production_sequence:
        if isinstance(other, production):
            return production_sequence(productions=[copy(self), copy(other)])
        else:
            return NotImplemented

    def get_name(self) -> str|None:
        return self.__name

    def set_name(self, name:str) -> production:
        self.__name = name
        return self

    def set_utility(self, utility:int) -> production:
        self.__utility = utility
        return self

    def set_reward(self, reward:float) -> production:
        self.__reward = reward
        return self

    def add_to_model(self, model:ACTRModel, production_name:str|None=None, utility:int=0, reward:float|None=None) -> production:
        if production_name:
            self.set_name(production_name)
        if utility:
            self.set_utility(utility)
        if reward:
            self.set_reward(reward)

        # fix for error in pyactr not converting the counter to str: `name = "unnamedrule" + productions.Productions._undefinedrulecounter` results in `TypeError: can only concatenate str (not "int") to str`
        if not self.get_name():
            self.set_name('unnamedrule' + str(model.productions._undefinedrulecounter))

        model.productionstring(
            name=self.__name if self.__name else '',
            string=str(self),
            utility=self.__utility,
            reward=self.__reward
        )

        return self
    

class production_sequence:
    def __init__(self, productions:list[production]):
        self.productions: list[production] = productions

    def __str__(self) -> str:
        return '\n\n'.join(map(str, self.productions))

    def __add__(self, other:production|production_sequence) -> production_sequence:
        if isinstance(other, production):
            new_productions = copy(self.productions)
            new_productions.append(other)
            return production_sequence(productions=new_productions)
        elif isinstance(other, production_sequence):
            new_productions = copy(self.productions)
            new_productions.extend(other.productions)
            return production_sequence(productions=new_productions)
        else:
            return NotImplemented
        
    def __radd__(self, other:production|production_sequence) -> production_sequence:
        if isinstance(other, production):
            new_productions = copy(self.productions)
            new_productions.insert(0, other)
            return production_sequence(productions=new_productions)
        elif isinstance(other, production_sequence):
            self.productions = other.productions + self.productions
            return self

    def add_to_model(self, model:ACTRModel) -> production_sequence:
        for production in self.productions:
            production.add_to_model(model)
        return self

