from simulation.Food import Food
from simulation.Wall import Wall
from simulation.Water import Water
from simulation.Location import Location
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
        self.check_pending_agent = None
        self.checked_agents = set()

    def set_game_environment(self, experiment_environment):
        """
        Override the experiment environment. That's because Middleman is created before the environment itself.

        Args:
            experiment_environment (Game): the environment for the agents
        """
        self.experiment_environment = experiment_environment

    def motor_input(self, key, current_agent):
        """
        Triggers environment functions based on key input.

        Wenn 'N' und der Agent hat noch nicht geprüft, setzt check_pending_agent.
        Wenn danach beliebige andere Taste (z.B. 'A'), und check_pending_agent == current_agent,
        wird check_if_won aufgerufen. Danach normaler Ablauf.

        Args:
            key (str): input key
            current_agent (AgentConstruct): the cognitive active agent
        """
        # 1) Wenn bereits check_pending_agent auf diesen Agenten zeigt,
        #    löse check_if_won aus statt der normalen Aktion
        if self.check_pending_agent == current_agent:
            # Wir wissen: der nächste Tastendruck nach 'N' gehört hierher
            self.check_if_won(current_agent, key)
            # Markiere Agent als geprüft, damit 'N' künftig nichts bewirkt
            self.checked_agents.add(current_agent)
            # Reset check_pending_agent
            self.check_pending_agent = None
            return

        # 2) Wenn Taste 'N' gedrückt und Agent wurde noch nicht geprüft → setze check_pending_agent
        if key == "N":
            if current_agent not in self.checked_agents:
                self.check_pending_agent = current_agent
            return  # danach keine Bewegung o.ä.

        # 3) Normale Tastenbefehle ausführen
        if key == "W":
            self.experiment_environment.move_agent_top(current_agent)
        elif key == "A":
            self.experiment_environment.move_agent_left(current_agent)
        elif key == "S":
            self.experiment_environment.move_agent_bottom(current_agent)
        elif key == "D":
            self.experiment_environment.move_agent_right(current_agent)
        elif key == "I":
            self.experiment_environment.sabotage(current_agent)
        elif key == "R":
            self.experiment_environment.repair(current_agent)

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
        rows, cols = len(matrix), len(matrix[0])

        # Wenn los = 0 oder größer als die Grid‐Dimensionen,
        # verwenden wir die komplette Karte als Sichtfeld:
        if los == 0 or los > cols or los > rows:
            x_los = cols
            y_los = rows
            off_x = off_y = 0
        else:
            # Fenstergröße = (2*los + 1) in jeder Richtung
            x_los = y_los = 2 * los + 1
            # Offset = los, damit Agent genau in der Mitte landet
            off_x = off_y = los

        new_triggers = []
        frame = {}
        visual_stimuli = [['' for _ in range(x_los)] for _ in range(y_los)]

        index = 0
        for i in range(y_los):
            for j in range(x_los):
                # Karte‐Koordinate = Agenten‐Zeile − off_y + i, Agenten‐Spalte − off_x + j
                mi = r - off_y + i
                mj = c - off_x + j

                # außerhalb der Karte?
                if mi < 0 or mi >= rows or mj < 0 or mj >= cols:
                    visual_stimuli[i][j] = '-'
                    continue

                # Ansonsten: alle Objekte in matrix[mi][mj] betrachten
                for element in matrix[mi][mj]:
                    if isinstance(element, AgentConstruct):
                        # Agenten‐Symbol aus agent_map holen
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

                    elif isinstance(element, Location):
                        sym = 'X'
                        new_triggers.append(sym)
                        frame[index] = {
                            "text": sym,
                            "position": (mi, mj)
                        }
                        visual_stimuli[i][j] = sym
                        index += 1

                    elif isinstance(element, Wall) or isinstance(element, Water):
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

    def check_if_won(self, agent, key_str):
        """
        Wird aufgerufen, wenn ein Agent nach 'N' eine Taste drückt.
        key_str entspricht dem Buchstaben (z.B. 'A', 'B', ...), der auf einen anderen Agenten zeigt.
        Wenn der referenzierte Agent den Namen 'Imposter' hat, beendet das Programm mit "YOU WON!!!".

        Args:
            agent (AgentConstruct): Der Agent, der 'N' gedrückt hatte.
            key_str (str): Der Buchstabe, der auf einen anderen Agenten verweist.
        """
        # 1) Hole das Agenten‐Mapping des ursprünglichen Agenten
        agent_map = agent.get_agent_dictionary()

        # 2) Prüfen, ob key_str im Dictionary existiert
        if key_str not in agent_map:
            # Ungültiger Buchstabe → nichts tun
            return

        # 3) Das referenzierte Agentenobjekt ermitteln
        other_agent = agent_map[key_str]["agent"]

        # 4) Prüfen, ob dessen Name "Imposter" ist
        if other_agent.name == "Imposter":
            # Simulation beenden mit Fehlermeldung
            raise RuntimeError("YOU WON!!!")
        else:
            raise RuntimeError(f"GAME OVER!!! {other_agent.name} was not the imposter.")