import pyactr
from pyactr.goals import Goal
from pyactr.chunks import Chunk
from pyactr.buffers import Buffer as PyactrBuffer
from simulation import LübeckACTR
from simulation.AgentConstruct import AgentConstruct

import random
import pandas as pd
from enum import Enum

from pyactr_oo_syntax.base.chunk import AdvChunk
from pyactr_oo_syntax.helpers.data_types import Buffer
from pyactr_oo_syntax.convenience.chunks import SimpleGoalChunk

from agents.abilities.pathfinding import (
    PathfindingImaginals,
    MovementDirection,
    FieldChunk, PathFieldChunk
)

from agents.abilities.pathfollowing import PathfollowingImaginals
from agents.abilities.observing import ObservingImaginals


class LogColor(Enum):
    DEFAULT = '\033[0m'
    DEBUGGING = '\033[31m'
    GENERAL_REASONING = '\033[32m'
    SPATIAL_AWARENESS = '\033[33m'
    VISION = '\033[34m'

def cprint(message:object, color:LogColor=LogColor.DEFAULT):
    """
    Prints a message in a specific color.

    Args:
        message (str): The message to print.
        color (str): The color to use for printing.
    """
    print(f"{color.value}{message}{LogColor.DEFAULT.value}")



class CharmanderAdapter:
    """
    Extending the agent with vision capabilities, spatial awareness, and general reasoning (like selecting a landmark randomly).
    """

    def __init__(self, environment:pyactr.Environment):
        """
        Args:
            agent_construct: pyactr.Environment gets later replaced by LübeckAACTR.simulation.AgentConstruct
        """
        self.agent_construct:AgentConstruct = environment # type: ignore

        self.previous_goal = None
        self.coordniate_format = '(vertical,horizontal)' # '(horizontal,vertical)' OR '(vertical,horizontal)'
        self.current_visual_field = pd.DataFrame()

    
    def extending_actr(self):
        """
        Adding vision capabilities, spatial awareness, and general reasoning (like selecting a landmark randomly).
        """        
        current_goal:Goal = LübeckACTR.get_goal(self.agent_construct.actr_agent) # type: ignore
        if current_goal == self.previous_goal: return # only do something when the goal state changes
        self.previous_goal = current_goal.copy()

        if SimpleGoalChunk(phase='start_from_beginning') in current_goal:
            ## INITIALIZE AGENT ##
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    AdvChunk(isa='lookahead',
                                             direction=None), 
                                    Buffer.IMAGINAL(PathfindingImaginals.LOOKAHEAD.value))
            visual_stimuli_df = self.parse_visual_stimuli()
            agent_position = visual_stimuli_df.at['A', 'position']
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    AdvChunk(isa=PathFieldChunk.isa,
                                             current=FieldChunk(x=agent_position[0], y=agent_position[1])), 
                                    Buffer.IMAGINAL(PathfindingImaginals.PATH_POSITION.value))
            cprint(f"ADAPTER (Charmander): Initializing direction imaginal and agent position. Agent Position = {agent_position}", LogColor.GENERAL_REASONING)

        elif SimpleGoalChunk(phase='choose_random_landmark') in current_goal:
            ## SELECT A RANDOM TARGET LANDMARK ##
            memory = self.agent_construct.actr_agent.decmem # type: ignore
            landmarks = []
            for chunk in memory:
                if chunk.typename == 'landmark':
                    landmark_location = {}
                    for slot in chunk:
                        landmark_location[slot[0]] = slot[1]
                    landmarks.append(landmark_location)
            selected_landmark = random.choice(landmarks)
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    AdvChunk(isa='target_landmark',
                                             landmark_field=FieldChunk(x=selected_landmark['x'], y=selected_landmark['y'])), 
                                    Buffer.IMAGINAL(PathfollowingImaginals.TARGET_LANDMARK.value))
            cprint(f"ADAPTER (Charmander): Choosing at random from known landmarks. Landmark Location = {selected_landmark}", LogColor.GENERAL_REASONING)
            
        elif SimpleGoalChunk(phase='move_heuristically') in current_goal:
            ## SET DIRECTION FOR PATHFINDING ##
            parsed_path_position = self.parse_imaginal_content(PathfindingImaginals.PATH_POSITION.value)
            delta_vertical = int(parsed_path_position['end']['y'][0]) - int(parsed_path_position['current']['y'][0]) if self.coordniate_format == '(horizontal,vertical)' else int(parsed_path_position['end']['x'][0]) - int(parsed_path_position['current']['x'][0])
            vertical = '' if delta_vertical == 0 else 'N' if delta_vertical < 0 else 'S'
            delta_horizontal = int(parsed_path_position['end']['x'][0]) - int(parsed_path_position['current']['x'][0]) if self.coordniate_format == '(horizontal,vertical)' else int(parsed_path_position['end']['y'][0]) - int(parsed_path_position['current']['y'][0])
            horizontal = '' if delta_horizontal == 0 else 'W' if delta_horizontal < 0 else 'E'
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    AdvChunk(isa='direction', 
                                             direction=vertical+horizontal), 
                                    Buffer.IMAGINAL(PathfindingImaginals.DIRECTION.value))
            cprint(f"ADAPTER (Charmander): Determining direction of landmark currently aiming for. Direction = {vertical+horizontal}", LogColor.SPATIAL_AWARENESS)

        elif SimpleGoalChunk(phase='follow_path') in current_goal:
            ## SET DIRECTION FOR PATHFOLLOWING ##
            parsed_path_position = self.parse_imaginal_content(PathfindingImaginals.PATH_POSITION.value)
            delta_vertical = int(parsed_path_position['next']['y'][0]) - int(parsed_path_position['current']['y'][0]) if self.coordniate_format == '(horizontal,vertical)' else int(parsed_path_position['next']['x'][0]) - int(parsed_path_position['current']['x'][0])
            vertical = '' if delta_vertical == 0 else 'N' if delta_vertical < 0 else 'S'
            delta_horizontal = int(parsed_path_position['next']['x'][0]) - int(parsed_path_position['current']['x'][0]) if self.coordniate_format == '(horizontal,vertical)' else int(parsed_path_position['next']['y'][0]) - int(parsed_path_position['current']['y'][0])
            horizontal = '' if delta_horizontal == 0 else 'W' if delta_horizontal < 0 else 'E'
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    AdvChunk(isa='direction', 
                                             direction=vertical+horizontal), 
                                    Buffer.IMAGINAL(PathfindingImaginals.DIRECTION.value))
            cprint(f"ADAPTER (Charmander): Determining direction of next field. Direction = {vertical+horizontal}", LogColor.SPATIAL_AWARENESS)


        elif SimpleGoalChunk(phase='lookahead') in current_goal:
            ## POPULATE VISUAL STIMULUS ##
            parsed_lookahead = self.parse_imaginal_content(PathfindingImaginals.LOOKAHEAD.value)
            direction = parsed_lookahead['direction']
            parsed_lookahead_stimulus = self.parse_visual_stimulus(direction)
            new_lookahead_chunk = AdvChunk(isa='lookahead', 
                                           direction=direction, 
                                           visual_stimulus=parsed_lookahead_stimulus)
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    new_lookahead_chunk, 
                                    Buffer.IMAGINAL(PathfindingImaginals.LOOKAHEAD.value))
            cprint(f"ADAPTER (Charmander): Determining visual stimulus in direction {direction}. Visual Stimulus = {parsed_lookahead_stimulus}", LogColor.VISION)

        elif SimpleGoalChunk(phase='memorize_step') in current_goal:
            ## UPDATE NEXT FIELD ##
            parsed_path_position = self.parse_imaginal_content(PathfindingImaginals.PATH_POSITION.value)
            parsed_lookahead = self.parse_imaginal_content(PathfindingImaginals.LOOKAHEAD.value)
            current_position = (int(parsed_path_position['current']['x'][0]), int(parsed_path_position['current']['y'][0]))
            direction = parsed_lookahead['direction']
            new_position = [
                current_position[0] + (-1 if direction == MovementDirection.LEFT.value else 1 if direction == MovementDirection.RIGHT.value else 0),
                current_position[1] + (-1 if direction == MovementDirection.UP.value else 1 if direction == MovementDirection.DOWN.value else 0)
            ] if self.coordniate_format == '(horizontal,vertical)' else [
                current_position[0] + (-1 if direction == MovementDirection.UP.value else 1 if direction == MovementDirection.DOWN.value else 0),
                current_position[1] + (-1 if direction == MovementDirection.LEFT.value else 1 if direction == MovementDirection.RIGHT.value else 0)
            ]
            new_position[0] = 19 if new_position[0] > 19 else 0 if new_position[0] < 0 else new_position[0]
            new_position[1] = 19 if new_position[1] > 19 else 0 if new_position[1] < 0 else new_position[1]
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent, 
                                    PathFieldChunk(end=FieldChunk(x=int(parsed_path_position['end']['x'][0]), y=int(parsed_path_position['end']['y'][0])),
                                                   current=FieldChunk(x=int(parsed_path_position['current']['x'][0]), y=int(parsed_path_position['current']['y'][0])),
                                                   next=FieldChunk(x=new_position[0], y=new_position[1])),
                                    Buffer.IMAGINAL(PathfindingImaginals.PATH_POSITION.value))
            cprint(f"ADAPTER (Charmander): Determining new field position. New Position = {new_position}", LogColor.SPATIAL_AWARENESS)

        elif SimpleGoalChunk(phase='check_landmark') in current_goal or SimpleGoalChunk(phase='check_landmark_pathfollowing') in current_goal:
            ## CHECK LANDMARK FOR DAMAGE ##            
            parsed_path_position = self.parse_imaginal_content(PathfindingImaginals.PATH_POSITION.value)
            is_damaged = LübeckACTR.check_location_damage(self.agent_construct)
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent,
                                    AdvChunk(isa='landmark_state',
                                             damaged=is_damaged),
                                    Buffer.IMAGINAL(PathfindingImaginals.LANDMARK_STATE.value))
            cprint(f"ADAPTER (Charmander): Determining landmark state. Damgaged = {is_damaged}", LogColor.VISION)

        elif SimpleGoalChunk(phase='start_observation') in current_goal:
            ## SAVE VISUAL FIELD TO KEEP TRACK OF ATTENDED / NOT ATTENDED STIMULI FOR OBSERVATION ##
            self.current_visual_field = self.parse_visual_stimuli().reset_index()
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent,
                                    AdvChunk(isa='observation',
                                             agent=None,
                                             alone=True),
                                    Buffer.IMAGINAL(ObservingImaginals.OBSERVATION.value))
            cprint(f"ADAPTER (Charmander):  Saving current visual field (to keep track of attended / not attended stimuli). Visual Field =\n{self.current_visual_field.T}", LogColor.VISION)
        
        elif SimpleGoalChunk(phase='observe_surroundings') in current_goal:
            ## CHOOSE A NOT YET ATTENED STIMULUS FOR OBSERVATION ##
            try:
                self.current_visual_field.reset_index(drop=True, inplace=True)
                visual_stimulus = self.current_visual_field.iloc[0][0]
                self.current_visual_field.drop(0, inplace=True)
            except IndexError:
                visual_stimulus = None
            LübeckACTR.set_imaginal(self.agent_construct.actr_agent,
                                    AdvChunk(isa='visual_clue',
                                             visual_stimulus=visual_stimulus),
                                    Buffer.IMAGINAL(ObservingImaginals.VISUAL_CLUE.value))
            cprint(f"ADAPTER (Charmander):  Choosing visual clue that was not yet attended. Visual Stimulus = {visual_stimulus}\nRemaining =\n{self.current_visual_field.T}", LogColor.VISION)


    def parse_imaginal_content(self, imaginal_suffix:str) -> dict:
        """
        Parse the contents of the imaginal identifiable with `imaginal_suffix` into a useable format.

        Args:
            imaginal_suffix (str): suffix added to `imaginal_` to identify imagonal

        Returns:
            dict: return imaginal content as dictionary
        """
        imaginal_buffer:PyactrBuffer = LübeckACTR.get_imaginal(self.agent_construct.actr_agent, Buffer.IMAGINAL(imaginal_suffix)) # type: ignore
        
        content = {}
        for slot in next(iter(imaginal_buffer)):
            if isinstance(slot_value := slot[1][0], Chunk):
                content[slot[0]] = slot_value._asdict()
            elif isinstance(slot_value, str):
                content[slot[0]] = slot_value
        return content
    

    def parse_visual_stimuli(self) -> pd.DataFrame:
        """
        Parse all viusal stimuli currently in the agent's field of vision and return it as a DataFrame.

        Returns:
            pd.DataFrame: visual stimuli as a DataFrame
        """
        visual_stimuli:dict = self.agent_construct.stimuli[0] # type: ignore
        visual_stimuli_df = pd.DataFrame.from_dict(visual_stimuli, orient='index')
        visual_stimuli_df.set_index('text', inplace=True)

        return visual_stimuli_df


    def parse_visual_stimulus(self, direction:str) -> str|None:
        """
        Parse visual stimuli currently in the agent's field of vision and return only the visual stimulus in the provided direction.

        Args:
            direction (str): direction for which to request the visual stimulus

        Returns:
            str|None: visual stimulus in requested direction, None if no stimulus is available (field is empty)
        """

        visual_stimuli_df = self.parse_visual_stimuli()

        agent_position = visual_stimuli_df.at['A', 'position']
        lookahead_position = (
            agent_position[0] + (-1 if direction == MovementDirection.LEFT.value else 1 if direction == MovementDirection.RIGHT.value else 0),
            agent_position[1] + (-1 if direction == MovementDirection.UP.value else 1 if direction == MovementDirection.DOWN.value else 0)
        ) if self.coordniate_format == '(horizontal,vertical)' else (
            agent_position[0] + (-1 if direction == MovementDirection.UP.value else 1 if direction == MovementDirection.DOWN.value else 0),
            agent_position[1] + (-1 if direction == MovementDirection.LEFT.value else 1 if direction == MovementDirection.RIGHT.value else 0)
        )

        visual_stimulus = visual_stimuli_df.index[visual_stimuli_df['position'] == lookahead_position]
        
        try:
            return visual_stimulus.item()
        except ValueError:
            return None
