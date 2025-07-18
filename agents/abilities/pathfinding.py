"""
(PY)ACT-R productions to add the ability to find a path to a given target landmark via heuristic and evasive / random movements,
remember the steps taken by adding them to declarative memory,
and repair damaged landmarks (either the target landmark on arrival or landmarks stumbled upon on the way). 

To add ability as a whole import pathfinding_prodseq and add to model with `.add_to_model(...)`.
"""

from __future__ import annotations
from enum import Enum
from pyactr_oo_syntax.helpers.data_types import Buffer, BufferStatus
from pyactr_oo_syntax.base.chunk import AdvChunk
from pyactr_oo_syntax.base.rule_and_production import production_sequence
from pyactr_oo_syntax.convenience.rules import *


class PathfindingImaginals(Enum):
    PATH_POSITION = 'path_position'
    DIRECTION = 'direction'
    LOOKAHEAD = 'lookahead'
    LANDMARK_STATE = 'landmark'


class MovementDirection(Enum):
    UP = 'W'
    DOWN = 'S'
    LEFT = 'A'
    RIGHT = 'D'


class FieldChunk(AdvChunk):
    isa = 'field'

    def __init__(self, x:int, y:int, **kwargs):
        super().__init__(isa=FieldChunk.isa, x=x, y=y, **kwargs)


class LandmarkChunk(AdvChunk):
    isa = 'landmark'

    def __init__(self, x:int, y:int):
        super().__init__(isa=LandmarkChunk.isa, x=x, y=y)


class PathFieldChunk(AdvChunk):
    isa = 'pathfield'

    def __init__(self, end:FieldChunk, current:FieldChunk, next:FieldChunk|None):
        super().__init__(isa=PathFieldChunk.isa, end=end, current=current, next=next)


class ItemChunk(AdvChunk):
    isa = 'item'

    def __init__(self, name:str, visual_stimulus:str):
        super().__init__(isa=ItemChunk.isa, name=name, visual_stimulus=visual_stimulus)


find_path_prodseq =\
(
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=FIELD',
                 end='~=FIELD',
                 next=None)
    >>
    is_simple_goal_(phase='move_heuristically')
).set_name('finding_path_next_unkown') +\
(
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=FIELD',
                 end='~=FIELD',
                 next=f"~{None}")
    >>
    is_simple_goal_(phase='move_randomly')
).set_name('finding_path_next_known_random').set_utility(8).set_reward(0) +\
(
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=FIELD',
                 end='~=FIELD',
                 next=f"~{None}")
    >>
    is_simple_goal_(phase='move_heuristically')
).set_name('finding_path_next_known_heuristic').set_utility(2).set_reward(0) +\
(
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=FIELD',
                 end='=FIELD')
    >>
    is_simple_goal_(phase='start_from_beginning') 
).set_name('finished_pathfinding')


__heuristic_movement_productions = []
for direction, keys in [('N', (MovementDirection.UP,)), 
                  ('NE', (MovementDirection.UP, MovementDirection.RIGHT)), 
                  ('E', (MovementDirection.RIGHT,)), 
                  ('SE', (MovementDirection.DOWN, MovementDirection.RIGHT)), 
                  ('S', (MovementDirection.DOWN,)), 
                  ('SW', (MovementDirection.DOWN, MovementDirection.LEFT)), 
                  ('W', (MovementDirection.LEFT,)), 
                  ('NW', (MovementDirection.UP, MovementDirection.LEFT))]:
    for key in keys:
        __heuristic_movement_productions.append(
            (
                is_simple_goal_(phase='move_heuristically') &
                subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.DIRECTION.value,
                             isa='direction',
                             direction=direction)
                >>
                subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                             isa='lookahead',
                             direction=key.value) &
                is_simple_goal_(phase='lookahead')
            ).set_name(f"move_{direction}_{key.value}").set_utility(int(10/len(keys))).set_reward(0)
        )
heuristic_movement_prodseq = production_sequence(__heuristic_movement_productions)


__random_movement_productions = []
for direction in [MovementDirection.UP, MovementDirection.DOWN, MovementDirection.LEFT, MovementDirection.RIGHT]:
    __random_movement_productions.append(
        (
            is_simple_goal_(phase='move_randomly')
            >>
            subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                         isa='lookahead',
                         direction=direction.value) &
            is_simple_goal_(phase='lookahead')
        ).set_name(f"move_randomly_{direction.value}").set_utility(2)
    )
random_movement_prodseq = production_sequence(__random_movement_productions)


general_movement_prodseq =\
(
    is_simple_goal_(phase='lookahead') &
    query_(buffer_name=Buffer.MANUAL, 
           status=BufferStatus.MANUAL.FREE) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                 isa='lookahead',
                 direction='=DIR',
                 visual_stimulus=None)                     
    >>
    is_simple_goal_(phase='memorize_step') &
    press_key_(key='=DIR')
).set_name('look_ahead_unobstructed') +\
(
    is_simple_goal_(phase='lookahead') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                 isa='lookahead',
                 visual_stimulus='~None')
    >>
    is_simple_goal_(phase='identify_obstruction')
).set_name('look_ahead_obstructed') +\
(
    is_simple_goal_(phase='identify_obstruction') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                 isa='lookahead',
                 visual_stimulus='=VISUAL_STIMULUS')                 
    >>
    is_simple_goal_(phase='identify') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa=ItemChunk.isa,
              visual_stimulus='=VISUAL_STIMULUS')
).set_name('retrieve_obstruction') +\
(
    is_simple_goal_(phase='identify') &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='obstacle')
    >>
    is_simple_goal_(phase='move_randomly')
).set_name('identify_obstacle').set_reward(-10) +\
(
    is_simple_goal_(phase='identify') &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='~obstacle')
    >>
    is_simple_goal_(phase='distinguish_non_obstacle') &
    is_retrieved_()
).set_name('identify_non_obstacle') +\
(    
    is_simple_goal_(phase='distinguish_non_obstacle') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='~landmark') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                 isa='lookahead',
                 direction='=DIR')   
    >>
    is_simple_goal_(phase='memorize_step') &
    press_key_(key='=DIR')
).set_name('identify_non_obstacle_non_landmark').set_reward(10)


landmark_repairing_prodseq =\
(
    is_simple_goal_(phase='distinguish_non_obstacle') &
    query_(buffer_name=Buffer.MANUAL, 
           status=BufferStatus.MANUAL.FREE) &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='landmark') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LOOKAHEAD.value,
                 isa='lookahead',
                 direction='=DIR')
    >>
    is_simple_goal_(phase='check_landmark') & 
    press_key_(key='=DIR')
).set_name('identify_landmark').set_reward(15) +\
(
    is_simple_goal_(phase='check_landmark') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LANDMARK_STATE.value,
                 isa='landmark_state',
                 damaged=False)
    >>
    is_simple_goal_(phase='find_path')
).set_name('determine_landmark_intact') +\
(
    is_simple_goal_(phase='check_landmark') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LANDMARK_STATE.value,
                 isa='landmark_state',
                 damaged=True)
    >>
    is_simple_goal_(phase='repair')
).set_name('determine_landmark_damaged') +\
(
    is_simple_goal_(phase='repair') &
    query_(buffer_name=Buffer.MANUAL, 
           status=BufferStatus.MANUAL.FREE)
    >>
    is_simple_goal_(phase='memorize_step') &
    press_key_(key='R')
).set_name('repair_landmark')


memorize_path_prodseq =\
(
    is_simple_goal_(phase='memorize_step') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=END',
                 current='=CURRENT',
                 next='=NEXT')
    >>
    is_simple_goal_(phase='update_path_field') &
    request_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
             isa=PathFieldChunk.isa,
             end='=END',
             current='=CURRENT',
             next='=NEXT')
).set_name('memorize_path_field_transition') +\
(
    is_simple_goal_(phase='update_path_field') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=END',
                 next='=NEXT')
    >>
    is_simple_goal_(phase='check_new_path_field') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa=PathFieldChunk.isa,
              end='=END',
              current='=NEXT')
).set_name('update_current_field') +\
(
    is_simple_goal_(phase='check_new_path_field') &
    query_(buffer_name=Buffer.RETRIEVAL, 
           status=BufferStatus.RETRIEVAL.FULL) &
    is_retrieved_(isa=PathFieldChunk.isa,
                  end='=END',     
                  current='=CURRENT',
                  next='=NEXT')
    >>
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=END',
                 current='=CURRENT',
                 next='=NEXT')
).set_name('retrieve_current_path_position') +\
(
    is_simple_goal_(phase='check_new_path_field') &
    query_(buffer_name=Buffer.RETRIEVAL, 
           status=BufferStatus.RETRIEVAL.ERROR) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=END',
                 next='=NEXT')
    >>
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=END',
                 current='=NEXT',
                 next=None)
).set_name('add_new_path_position')


pathfinding_prodseq = find_path_prodseq + heuristic_movement_prodseq + random_movement_prodseq + general_movement_prodseq + landmark_repairing_prodseq + memorize_path_prodseq
