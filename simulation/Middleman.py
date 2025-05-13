from simulation.Food import Food
from simulation.Wall import Wall
from simulation.AgentConstruct import AgentConstruct

class Middleman:
    """
    Handles interaction between environment and agents. This includes visual outputs and motor inputs.

    Attributes:
        simulation (Simulation): Tha parent simulation
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
            new_triggers (list of str): symbols for each visible object
            stimuli (list of dict): list with exactly one dict mapping unique stimulus-IDs
                                  to {'text', 'position', 'color', 'value'}
        """
        matrix = self.experiment_environment.level_matrix
        r, c = self.experiment_environment.find_agent(agent)
        if r is None:
            return None, None

        agent_map = agent.get_agent_dictionary()
        rows, cols = len(matrix), len(matrix[0])

        # Field of view (los)
        los = agent.los
        if los == 0 or los > cols or los > rows:
            x_los, y_los = cols, rows
        else:
            x_los = y_los = los

        off_y, off_x = y_los // 2, x_los // 2

        # Prepare Rückgabe
        new_triggers = []
        frame = {}  # Hier sammeln wir alle Stimuli für *ein* Zeitfenster

        # (optional) Für Debug/Visualisierung
        visual_stimuli = [['' for _ in range(x_los)] for _ in range(y_los)]

        for i in range(y_los):
            for j in range(x_los):
                mi, mj = r - off_y + i, c - off_x + j
                if mi < 0 or mi >= rows or mj < 0 or mj >= cols:
                    visual_stimuli[i][j] = 'X'
                    continue

                for element in matrix[mi][mj]:
                    if isinstance(element, AgentConstruct):
                        # Welches Symbol gehört zu diesem Agenten?
                        for sym, info in agent_map.items():
                            if info["agent"] == element:
                                if sym not in new_triggers:
                                    new_triggers.append(sym)
                                frame[sym] = {
                                    "text": sym,
                                    "position": (mi, mj),
                                    "color": "blue",
                                    "value": sym
                                }
                                visual_stimuli[i][j] = sym
                                break

                    elif isinstance(element, Food):
                        sym = 'Y'
                        if sym not in new_triggers:
                            new_triggers.append(sym)
                        frame[sym] = {
                            "text": sym,
                            "position": (mi, mj),
                            "color": "red",
                            "value": sym
                        }
                        visual_stimuli[i][j] = sym

                    elif isinstance(element, Wall):
                        sym = 'Z'
                        if sym not in new_triggers:
                            new_triggers.append(sym)
                        frame[sym] = {
                            "text": sym,
                            "position": (mi, mj),
                            "color": "black",
                            "value": sym
                        }
                        visual_stimuli[i][j] = sym

        # Für (optionale) Visualisierung im Agent-Objekt
        agent.visual_stimuli = visual_stimuli

        # PyACT-R erwartet: List[Dict[id → attributes]]
        stimuli = [frame]
        return new_triggers, stimuli
