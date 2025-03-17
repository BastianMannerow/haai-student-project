import random
import string
from simulation.Food import Food
from simulation.Wall import Wall
from simulation.AgentConstruct import AgentConstruct

class Middleman:
    def __init__(self, simulation, print_middleman):
        self.simulation = simulation
        self.experiment_environment = None
        self.print_middleman = print_middleman

    def set_game_environment(self, experiment_environment):
        print("SUCCESS")
        print(experiment_environment)
        self.experiment_environment = experiment_environment

    def motor_input(self, key, current_agent):
        if key == "W":
            self.experiment_environment.move_agent_top(current_agent)

        elif key == "A":
            self.experiment_environment.move_agent_left(current_agent)

        elif key == "S":
            self.experiment_environment.move_agent_bottom(current_agent)

        elif key == "D":
            self.experiment_environment.move_agent_right(current_agent)

    def get_agent_stimulus(self, agent):
        matrix = self.experiment_environment.level_matrix
        r, c = self.experiment_environment.find_agent(agent)
        agent_stimuli_dictionary = agent.get_agent_dictionary()

        new_triggers = []
        new_text = {}

        rows = len(matrix)
        cols = len(matrix[0])

        # Initialize the visual stimuli matrix with empty strings
        visual_stimuli = [['' for _ in range(5)] for _ in range(5)]

        index = 0  # To keep track of the index for new_text

        for i in range(5):
            for j in range(5):
                matrix_i = r - 2 + i
                matrix_j = c - 2 + j
                if matrix_i < 0 or matrix_i >= rows or matrix_j < 0 or matrix_j >= cols:
                    visual_stimuli[i][j] = 'X'
                else:
                    elements = matrix[matrix_i][matrix_j]
                    for element in elements:
                        if isinstance(element, AgentConstruct):
                            for key, value in agent_stimuli_dictionary.items():
                                if value == element:
                                    new_triggers.append(key)
                                    new_text[index] = {'text': key, 'position': (matrix_i, matrix_j)}
                                    visual_stimuli[i][j] = key
                                    index += 1
                                    break
                        elif isinstance(element, Food):
                            if 'Y' not in new_triggers:
                                new_triggers.append('Y')
                            new_text[index] = {'text': 'Y', 'position': (matrix_i, matrix_j)}
                            visual_stimuli[i][j] = 'Y'
                            index += 1
                        elif isinstance(element, Wall):
                            if 'Z' not in new_triggers:
                                new_triggers.append('Z')
                            new_text[index] = {'text': 'Z', 'position': (matrix_i, matrix_j)}
                            visual_stimuli[i][j] = 'Z'
                            index += 1


        agent.visual_stimuli = visual_stimuli
        return new_triggers, [new_text]
