import pyactr
from pyactr_oo_syntax.convenience.rules import *

from agents.abilities.pathfinding import (
    PathfindingImaginals,
    FieldChunk, LandmarkChunk, PathFieldChunk, ItemChunk,
    pathfinding_prodseq
)

from agents.abilities.pathfollowing import (
    PathfollowingImaginals,
    pathfollowing_prodseq
)

from agents.abilities.observing import (
    ObservingImaginals,
    observing_prodseq
)


class Charmander:
    
    def __init__(self, environment: pyactr.Environment):
        self.this_agent_key = None
        self.other_agents_key_list = None

        self.environ = environment
        self.actr_agent = pyactr.ACTRModel(
            environment = self.environ, 
            motor_prepared = True, 
            automatic_visual_search = False, 
            subsymbolic = True
        )

        self.initial_goal = SimpleGoalChunk(phase='start_from_beginning')
        self.coordniate_format = '(vertical,horizontal)' # '(horizontal,vertical)' OR '(vertical,horizontal)'


    def build_agent(self, agent_list:list[str]) -> pyactr.ACTRModel:
        self.configure_agent(agent_list)
        self.setup_imaginals()

        self.add_initial_knowledge()
        self.add_productions()

        return self.actr_agent


    def configure_agent(self, agent_list:list[str]):
        self.this_agent_key = agent_list[0]
        self.other_agents_key_list = agent_list[1:]

        self.actr_agent.model_parameters['utility_noise'] = 5
        self.actr_agent.model_parameters['baselevel_learning'] = False


    def setup_imaginals(self):
        self.imaginals = {}

        for imaginal_enum in (PathfindingImaginals, PathfollowingImaginals, ObservingImaginals):
            for imaginal_name in imaginal_enum:
                self.imaginals[imaginal_name.value] = self.actr_agent.set_goal(
                        name=Buffer.IMAGINAL(imaginal_name.value), 
                        delay=0
                    )


    def add_initial_knowledge(self):
        self.add_landmark_knowledge()
        self.add_object_knowledge()
        
        # for DEBUGGING the subtasks (semi-)independently of each other:
        # self.test_pathfollowing()
        # self.test_pathfinding()
        # self.test_observing()

    
    def add_landmark_knowledge(self):
        for landmark_location in ((1,8), (2,1), (2,17), (8,7), (15,2), (16,18)):
            LandmarkChunk(
                x = landmark_location[0] if self.coordniate_format == '(horizontal,vertical)' else landmark_location[1], 
                y = landmark_location[1] if self.coordniate_format == '(horizontal,vertical)' else landmark_location[0]
            ).add_to_decmem(self.actr_agent)


    def add_object_knowledge(self):
        visual_stimuli_associations = [('obstacle', 'Z'), ('landmark', 'X'), ('self', self.this_agent_key)]
        if self.other_agents_key_list:
            visual_stimuli_associations.extend([('other_agent', agent_key) for agent_key in self.other_agents_key_list])
        
        for name, visual_stimulus in visual_stimuli_associations:
            ItemChunk(
                name=name,
                visual_stimulus=visual_stimulus
            ).add_to_decmem(self.actr_agent)


    def test_pathfollowing(self):
        self.initial_goal = SimpleGoalChunk(phase='start_pathfollowing')
        self.imaginals[PathfindingImaginals.PATH_POSITION.value].add(
            PathFieldChunk(
                end = FieldChunk(x=17, y=2),
                current = FieldChunk(x=19, y=17), 
                next = None
            )
        )
        self.imaginals[PathfollowingImaginals.TARGET_LANDMARK.value].add(
            AdvChunk(
                isa = 'target_landmark',
                landmark_field = FieldChunk(x=17, y=2)
            )
        )

        field_coordinates = (
            (19,17),(18,17),(17,17),(16,17),(15,17),(14,17),
            (14,16),(14,15),(14,14),(14,13),(14,12),(14,11),(14,10),(14,9),(14,8),(14,7),(14,6),(14,5),(14,4),(14,3),(14,2),
            (15,2),(16,2),(17,2)
        )
        for i in range(len(field_coordinates)):
            end_field = FieldChunk(x=field_coordinates[-1][0], y=field_coordinates[-1][1]).add_to_decmem(self.actr_agent)
            current_field = FieldChunk(x=field_coordinates[i][0], y=field_coordinates[i][1]).add_to_decmem(self.actr_agent)
            next_field = None if i == (len(field_coordinates) - 1) else FieldChunk(x=field_coordinates[i+1][0], y=field_coordinates[i+1][1]).add_to_decmem(self.actr_agent)
            self.actr_agent.decmem.add(pyactr.makechunk(
                nameofchunk=f"path_field_chunk_{i}",
                typename=PathFieldChunk.isa,
                end=end_field,
                current=current_field,
                next=next_field
            ))


    def test_pathfinding(self):
        self.initial_goal = SimpleGoalChunk(phase='find_path')
        self.imaginals[PathfindingImaginals.PATH_POSITION.value].add(
            PathFieldChunk(
                end = FieldChunk(x=8, y=1), # (x=18, y=16)
                current = FieldChunk(x=19, y=17), 
                next = None
            )
        )
        self.imaginals[PathfindingImaginals.LOOKAHEAD.value].add(
            AdvChunk(
                isa = 'lookahead',
                direction = None
            )
        )


    def test_observing(self):
        self.initial_goal = SimpleGoalChunk(phase='start_pathfollowing')
        self.imaginals[PathfindingImaginals.PATH_POSITION.value].add(
            PathFieldChunk(
                end = FieldChunk(x=18, y=16),
                current = FieldChunk(x=19, y=17), 
                next = None
            )
        )
        self.imaginals[PathfollowingImaginals.TARGET_LANDMARK.value].add(
            AdvChunk(
                isa = 'target_landmark',
                landmark_field = FieldChunk(x=18, y=16)
            )
        )

        field_coordinates = (
            (19,17),(18,17),(18,16)
        )
        for i in range(len(field_coordinates)):
            end_field = FieldChunk(x=field_coordinates[-1][0], y=field_coordinates[-1][1]).add_to_decmem(self.actr_agent)
            current_field = FieldChunk(x=field_coordinates[i][0], y=field_coordinates[i][1]).add_to_decmem(self.actr_agent)
            next_field = None if i == (len(field_coordinates) - 1) else FieldChunk(x=field_coordinates[i+1][0], y=field_coordinates[i+1][1]).add_to_decmem(self.actr_agent)
            self.actr_agent.decmem.add(pyactr.makechunk(
                nameofchunk=f"path_field_chunk_{i}",
                typename=PathFieldChunk.isa,
                end=end_field,
                current=current_field,
                next=next_field
            ))


    def add_productions(self):
        (
            is_simple_goal_(phase='start_from_beginning')
            >>
            is_simple_goal_(phase='choose_random_landmark')
        ).add_to_model(self.actr_agent, 'initialize_agent')

        (
            is_simple_goal_(phase='choose_random_landmark')
            >>
            is_simple_goal_(phase='start_pathfollowing')
        ).add_to_model(self.actr_agent, 'select_random_landmark_as_target')

        pathfinding_prodseq.add_to_model(self.actr_agent)
        pathfollowing_prodseq.add_to_model(self.actr_agent)
        observing_prodseq.add_to_model(self.actr_agent)

