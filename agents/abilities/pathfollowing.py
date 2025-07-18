"""
(PY)ACT-R productions to add the ability to follow paths that were previously saved to declarative memory
and repair a potentially damaged landmark once the agent arrives at the target landmark. 

To add ability as a whole import pathfollowing_prodseq and add to model with `.add_to_model(...)`.
"""

from __future__ import annotations
from enum import Enum
from pyactr_oo_syntax.helpers.data_types import Buffer, BufferStatus
from pyactr_oo_syntax.base.rule_and_production import production_sequence
from pyactr_oo_syntax.convenience.rules import *

from agents.abilities.pathfinding import PathFieldChunk, PathfindingImaginals, MovementDirection

class PathfollowingImaginals(Enum):
    TARGET_LANDMARK = 'goal_landmark'


remembering_path_prodseq =\
(
    is_simple_goal_(phase='start_pathfollowing') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfollowingImaginals.TARGET_LANDMARK.value,
                 isa='target_landmark',
                 landmark_field='=LANDMARK') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=CURRENT')
    >>
    is_simple_goal_(phase='update_current_pathfollowing_position') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa=PathFieldChunk.isa,
              current='=CURRENT',
              end='=LANDMARK')
).set_name('start_following_path') +\
(
    is_simple_goal_(phase='update_current_pathfollowing_position') &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL) &
    is_retrieved_(isa=PathFieldChunk.isa,
                  current='=CURRENT',
                  end='=END',
                  next='=NEXT')
    >>    
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 current='=CURRENT',
                 end='=END',
                 next='=NEXT') &
    is_simple_goal_(phase='check_arrived')
).set_name('updating_pathfollowing_position') +\
(
    is_simple_goal_(phase='update_current_pathfollowing_position') &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.ERROR) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfollowingImaginals.TARGET_LANDMARK.value,
                 isa='target_landmark',
                 landmark_field='=LANDMARK')
    >>
    is_simple_goal_(phase='find_path') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 end='=LANDMARK')
).set_name('change_to_pathfinding') +\
(
    is_simple_goal_(phase='check_arrived') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                isa=PathFieldChunk.isa,
                current='=FIELD',
                end='=FIELD')
    >>
    is_simple_goal_(phase='check_landmark_pathfollowing')
).set_name(f"finished_pathfollowing") +\
(
    is_simple_goal_(phase='check_arrived') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                isa=PathFieldChunk.isa,
                current='=FIELD',
                end='~=FIELD')
    >>
    is_simple_goal_(phase='follow_path')
).set_name(f"continue_pathfollowing") +\
(
    is_simple_goal_(phase='update_pathfollowing_field') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.PATH_POSITION.value,
                 isa=PathFieldChunk.isa,
                 next='=NEXT',
                 end='=END')
    >>
    is_simple_goal_(phase='update_current_pathfollowing_position') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa=PathFieldChunk.isa,
              current='=NEXT',
              end='=END')
).set_name('update_pathfollowing_field')


__guided_movement_productions = []
for direction, key in [('N', MovementDirection.UP), 
                       ('E', MovementDirection.RIGHT),  
                       ('S', MovementDirection.DOWN), 
                       ('W', MovementDirection.LEFT)]:
    
    __guided_movement_productions.append(
        (
            is_simple_goal_(phase='follow_path') &
            query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
            subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.DIRECTION.value,
                        isa='direction',
                        direction=direction)
            >>
            is_simple_goal_(phase='update_pathfollowing_field') &
            press_key_(key=key.value)
        ).set_name(f"take_step_along_path_{direction}")
    )
guided_movement_prodseq = production_sequence(__guided_movement_productions)


landmark_repairing_prodseq =\
(
    is_simple_goal_(phase='check_landmark_pathfollowing') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LANDMARK_STATE.value,
                 isa='landmark_state',
                 damaged=False)
    >>
    is_simple_goal_(phase='start_from_beginning')
).set_name('determine_landmark_intact') +\
(
    is_simple_goal_(phase='check_landmark_pathfollowing') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=PathfindingImaginals.LANDMARK_STATE.value,
                 isa='landmark_state',
                 damaged=True)
    >>
    is_simple_goal_(phase='repair_pathfollowing')
).set_name('determine_landmark_damaged_pathfollowing') +\
(
    is_simple_goal_(phase='repair_pathfollowing') &
    query_(buffer_name=Buffer.MANUAL, 
           status=BufferStatus.MANUAL.FREE)
    >>
    is_simple_goal_(phase='start_observation') &
    press_key_(key='R')
).set_name('repair_landmark_pathfollowing')


pathfollowing_prodseq = remembering_path_prodseq + guided_movement_prodseq + landmark_repairing_prodseq
