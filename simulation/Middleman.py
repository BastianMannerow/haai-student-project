from simulation.Food import Food
from simulation.Wall import Wall
from simulation.AgentConstruct import AgentConstruct

class Middleman:
    """
    Handles interaction between environment and agents. This includes visual outputs and motor inputs.

    Attributes:
        simulation (Simulation): The parent simulation
        experiment_environment (Game): The environment for the agents
        print_middleman (bool): Logging for debugging
    """

    def __init__(self, simulation, print_middleman):
        self.simulation = simulation
        self.experiment_environment = None
        self.print_middleman = print_middleman

    def set_game_environment(self, experiment_environment):
        """
        Override the experiment environment. That's because Middleman is created before the environment itself.

        Args:
            experiment_environment (Game): the environment for the agents
        """
        self.experiment_environment = experiment_environment

    def motor_input(self, key, current_agent):
        """
        Triggers environment functions based on key input

        Args:
            key (str): input key
            current_agent (AgentConstruct): the cognitive active agent
        """
        if key == "W":
            self.experiment_environment.move_agent_top(current_agent)
        elif key == "A":
            self.experiment_environment.move_agent_left(current_agent)
        elif key == "S":
            self.experiment_environment.move_agent_bottom(current_agent)
        elif key == "D":
            self.experiment_environment.move_agent_right(current_agent)

    def get_agent_stimulus(self, agent):
        """
        Creates new visual stimuli based on the environment, the agent's ID map, and its field of view.

        Args:
            agent (AgentConstruct): the cognitive active agent

        Returns:
            new_triggers (list of str): symbols for each visible object (inkl. Duplikate)
            stimuli (list of dict): list mit genau einem dict, das fortlaufend
                                    ge-ID-t Stimuli mappt auf {'text', 'position'}
        """
        matrix = self.experiment_environment.level_matrix
        r, c = self.experiment_environment.find_agent(agent)
        if r is None:
            return None, None

        agent_map = agent.get_agent_dictionary()
        rows, cols = len(matrix), len(matrix[0])

        # Field of view
        los = agent.los
        if los == 0 or los > cols or los > rows:
            x_los, y_los = cols, rows
        else:
            x_los = y_los = los

        off_y, off_x = y_los // 2, x_los // 2

        new_triggers = []
        frame = {}
        visual_stimuli = [['' for _ in range(x_los)] for _ in range(y_los)]

        index = 0
        for i in range(y_los):
            for j in range(x_los):
                mi, mj = r - off_y + i, c - off_x + j

                # outside the box
                if mi < 0 or mi >= rows or mj < 0 or mj >= cols:
                    visual_stimuli[i][j] = 'X'
                    continue

                for element in matrix[mi][mj]:
                    if isinstance(element, AgentConstruct):
                        for sym, info in agent_map.items():
                            if info["agent"] == element:
                                new_triggers.append(sym)
                                frame[index] = {
                                    "text": sym,
                                    "position": (mi, mj)
                                }
                                visual_stimuli[i][j] = sym
                                index += 1
                                break

                    elif isinstance(element, Food):
                        sym = 'Y'
                        new_triggers.append(sym)
                        frame[index] = {
                            "text": sym,
                            "position": (mi, mj)
                        }
                        visual_stimuli[i][j] = sym
                        index += 1

                    elif isinstance(element, Wall):
                        sym = 'Z'
                        new_triggers.append(sym)
                        frame[index] = {
                            "text": sym,
                            "position": (mi, mj)
                        }
                        visual_stimuli[i][j] = sym
                        index += 1

        agent.visual_stimuli = visual_stimuli
        stimuli = [frame]
        return new_triggers, stimuli
