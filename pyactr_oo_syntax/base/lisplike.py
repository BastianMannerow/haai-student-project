"""
LISP-like notation for creating object-based rules and productions.
"""

from typing import Callable

from pyactr_oo_syntax.base.rule_and_production import rule_
from pyactr_oo_syntax.helpers.data_types import Buffer, RuleType


class p: # lisp ACT-R: +
    @staticmethod
    def create_request_generator(buffer_name:Buffer|Callable[[str|None],str]):
        def generate_request(imaginal_buffer_name:str|None=None, isa:str|None=None, **kwargs):
            return rule_(rule_type=RuleType.REQUEST, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=isa, **kwargs)
        return staticmethod(generate_request)
        
    GOAL_ = create_request_generator(buffer_name=Buffer.GOAL)
    RETRIEVAL_ = create_request_generator(buffer_name=Buffer.RETRIEVAL)
    VISUAL_ = create_request_generator(buffer_name=Buffer.VISUAL)
    VISUAL_LOCATION_ = create_request_generator(buffer_name=Buffer.VISUAL_LOCATION)
    MANUAL_ = create_request_generator(buffer_name=Buffer.MANUAL)
    IMAGINAL_ = create_request_generator(buffer_name=Buffer.IMAGINAL)


class e: # lisp ACT-R: =
    @staticmethod
    def create_subsumption_generator(buffer_name:Buffer|Callable[[str|None],str]):
        def generate_subsumption(imaginal_buffer_name:str|None=None, isa:str|None=None, **kwargs):
            return rule_(rule_type=RuleType.SUBSUMPTION, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=isa, **kwargs)
        return staticmethod(generate_subsumption)
        
    GOAL_ = create_subsumption_generator(buffer_name=Buffer.GOAL)
    RETRIEVAL_ = create_subsumption_generator(buffer_name=Buffer.RETRIEVAL)
    VISUAL_ = create_subsumption_generator(buffer_name=Buffer.VISUAL)
    VISUAL_LOCATION_ = create_subsumption_generator(buffer_name=Buffer.VISUAL_LOCATION)
    MANUAL_ = create_subsumption_generator(buffer_name=Buffer.MANUAL)
    IMAGINAL_ = create_subsumption_generator(buffer_name=Buffer.IMAGINAL)


class q: # lisp ACT-R: ?
    @staticmethod
    def create_status_generator(buffer_name:Buffer|Callable[[str|None],str]):
        def generate_status(imaginal_buffer_name:str|None=None, state:str|None=None, buffer:str|None=None, error:str|None=None, **kwargs):
            return rule_(rule_type=RuleType.QUERY, buffer_name=buffer_name, imaginal_buffer_name=imaginal_buffer_name, isa=None, state=state, buffer=buffer, error=error, **kwargs)
        return staticmethod(generate_status)

    GOAL_ = create_status_generator(Buffer.GOAL)
    RETRIEVAL_ = create_status_generator(buffer_name=Buffer.RETRIEVAL)
    VISUAL_ = create_status_generator(buffer_name=Buffer.VISUAL)
    VISUAL_LOCATION_ = create_status_generator(buffer_name=Buffer.VISUAL_LOCATION)
    MANUAL_ = create_status_generator(buffer_name=Buffer.MANUAL)
    IMAGINAL_ = create_status_generator(buffer_name=Buffer.IMAGINAL)   


class t: # lisp ACT-R: ~
    @staticmethod
    def create_flush_generator(buffer_name:Buffer|Callable[[str|None],str]):
        return staticmethod(lambda: rule_(rule_type=RuleType.FLUSH, buffer_name=buffer_name))
        
    GOAL_ = create_flush_generator(buffer_name=Buffer.GOAL)
    RETRIEVAL_ = create_flush_generator(buffer_name=Buffer.RETRIEVAL)
    VISUAL_ = create_flush_generator(buffer_name=Buffer.VISUAL)
    VISUAL_LOCATION_ = create_flush_generator(buffer_name=Buffer.VISUAL_LOCATION)
    MANUAL_ = create_flush_generator(buffer_name=Buffer.VISUAL_LOCATION)
    IMAGINAL_ = create_flush_generator(buffer_name=Buffer.IMAGINAL)
