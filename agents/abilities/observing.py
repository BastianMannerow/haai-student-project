"""
(PY)ACT-R productions to add the ability to observe if other agents are near a damaged landmark 
and (with utility 8 to 2) nominate an imposter if an observation a an agent being alone near a damaged landmark is available. 

To add ability as a whole import observing_prodseq and add to model with `.add_to_model(...)`.
"""

from __future__ import annotations
from enum import Enum
from pyactr_oo_syntax.helpers.data_types import Buffer, BufferStatus
from pyactr_oo_syntax.convenience.rules import *

from agents.abilities.pathfinding import ItemChunk

class ObservingImaginals(Enum):
    VISUAL_CLUE = 'visual_clue'
    OBSERVATION = 'observation'


detection_prodseq =\
(
    is_simple_goal_(phase='start_observation') 
    >>
    is_simple_goal_(phase='observe_surroundings') 
).set_name('start_observation') +\
(
    is_simple_goal_(phase='observe_surroundings') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.VISUAL_CLUE.value,
                 isa='visual_clue',
                 visual_stimulus='~None')
    >>
    is_simple_goal_(phase='check_visual_clue')
).set_name('check_visual_clue_remaining') +\
(
    is_simple_goal_(phase='observe_surroundings') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.VISUAL_CLUE.value,
                 isa='visual_clue',
                 visual_stimulus=None)
    >>
    is_simple_goal_(phase='remember_observation')
).set_name('finished_detection') +\
(
    is_simple_goal_(phase='check_visual_clue') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.VISUAL_CLUE.value,
                 isa='visual_clue',
                 visual_stimulus='=S')
    >>
    is_simple_goal_(phase='assess_visual_clue') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa=ItemChunk.isa,
              visual_stimulus='=S')
).set_name('observing_visual_stimulus') +\
(
    is_simple_goal_(phase='assess_visual_clue') & 
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
                 isa='observation',
                 agent=None) &
    query_(buffer_name=Buffer.RETRIEVAL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='other_agent',
                  visual_stimulus='=ID')
    >>
    is_simple_goal_(phase='observe_surroundings') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
                 isa='observation',
                 agent='=ID')
).set_name('assess_first_agent') +\
(
    is_simple_goal_(phase='assess_visual_clue') & 
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
                 isa='observation',
                 agent='~None') &
    query_(buffer_name=Buffer.RETRIEVAL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='other_agent',
                  visual_stimulus='=ID')
    >>
    is_simple_goal_(phase='remember_observation') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
                 isa='observation',
                 alone=False)
).set_name('assess_additional_agent') +\
(
    is_simple_goal_(phase='assess_visual_clue') &
    query_(buffer_name=Buffer.RETRIEVAL) &
    is_retrieved_(isa=ItemChunk.isa,
                  name='~other_agent')
    >>
    is_simple_goal_(phase='observe_surroundings')
).set_name('assess_irrelevant') +\
(
    is_simple_goal_(phase='remember_observation') &
    subsumption_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
                 isa='observation',
                 agent='=AGENT',
                 alone='=ALONE')
    >>
    is_simple_goal_(phase='check_observations') &
    request_(buffer_name=Buffer.IMAGINAL, imaginal_buffer_name=ObservingImaginals.OBSERVATION.value,
             isa='observation',
             agent='=AGENT',
             alone='=ALONE')
).set_name('finished_observation')


nomination_prodseq =\
(
    is_simple_goal_(phase='check_observations')
    >>
    is_simple_goal_(phase='assess_confidence') &
    flush_(buffer_name=Buffer.RETRIEVAL) &
    retrieve_(isa='observation',
              agent='~None',
              alone=True)
).set_name('check_observations') +\
(
    is_simple_goal_(phase='assess_confidence') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL)
    >>
    is_simple_goal_(phase='nominate') &
    is_retrieved_() &
    press_key_(key='N')
).set_name('observation_confidence_high').set_utility(8) +\
(
    is_simple_goal_(phase='nominate') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    is_retrieved_(isa='observation',
                  agent='=ID')
    >>
    is_simple_goal_(phase='wait_for_nomination_to_be_completed') &
    press_key_(key='=ID')
).set_name('nominate_imposter') +\
(
    is_simple_goal_(phase='assess_confidence') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE) &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.FULL)
    >>
    is_simple_goal_(phase='start_from_beginning')
).set_name('observation_confidence_mid').set_utility(2) +\
(
    is_simple_goal_(phase='assess_confidence') &
    query_(buffer_name=Buffer.RETRIEVAL, status=BufferStatus.RETRIEVAL.ERROR)
    >>
    is_simple_goal_(phase='start_from_beginning')
).set_name('observation_confidence_low') +\
(
    is_simple_goal_('wait_for_nomination_to_be_completed') &
    query_(buffer_name=Buffer.MANUAL, status=BufferStatus.MANUAL.FREE)
    >>
    flush_(buffer_name=Buffer.GOAL)
).set_name('nomination_completed')


observing_prodseq = detection_prodseq + nomination_prodseq
