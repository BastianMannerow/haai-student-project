from gui.GUI import MatrixWorldGUI
from simulation.Wall import Wall
from simulation.Water import Water
from simulation.Location import Location

class Game:
    """
    The matrix environment.

    Attributes:
        gui (GUI from TK): The gui, which displays the game
        cage (dict): Hält eingesperrte Agenten mit ihrem actr_time-Timestamp
    """

    def __init__(self, gui, level_matrix):
        """
        Args:
            gui: displays the game
            level_matrix: 2D-Liste mit Zellinhalten (Agenten, Walls, Water, Location, Food, etc.)
        """
        # Jedes Level-Element in eine Liste packen, falls es noch keine ist
        self.level_matrix = [
            [cell if isinstance(cell, list) else [cell] for cell in row]
            for row in level_matrix
        ]

        # Cage initialisieren: { agent_instance: timestamp }
        self.cage = {}

        # GUI erstellen und erste Aktualisierung
        self.gui = MatrixWorldGUI(self, gui)
        self.gui.update()

        # Level-Matrix nochmals daraufhin aufbauen, dass alle Einträge Listen sind
        self.level_matrix = [
            [cell if isinstance(cell, list) else [cell] for cell in row]
            for row in level_matrix
        ]

    def find_agent(self, agent):
        for r, row in enumerate(self.level_matrix):
            for c, cell in enumerate(row):
                if agent in cell:
                    return r, c
        return None, None

    def move_agent(self, agent, dr, dc):
        """
        Bewegt den Agenten um (dr, dc), falls möglich:
        - Zelle ist innerhalb der Grenzen
        - Zelle enthält keine Wall- oder Water-Objekte
        - Agent ist nicht noch im Cage (oder Cage-Zeit ist >= 8 Sekunden vorbei)

        Returns:
            bool: True, wenn die Bewegung erfolgreich war, sonst False.
        """
        # Wenn Agent im Cage ist: erst prüfen, ob 8 Sekunden vergangen sind
        if agent in self.cage:
            trapped_time = self.cage[agent]
            current_time = agent.actr_time
            if (current_time - trapped_time) < 8:
                # Noch nicht genug Zeit zum Freilassen
                return False
            else:
                # 8 Sekunden vorbei → Agent frei lassen
                del self.cage[agent]

        position = self.find_agent(agent)
        if position is None:
            return False

        r, c = position
        nr, nc = r + dr, c + dc

        # Check if new position is within bounds
        if not (0 <= nr < len(self.level_matrix) and 0 <= nc < len(self.level_matrix[0])):
            return False

        # Check if new position contains a Wall oder Water
        if any(isinstance(obj, (Wall, Water)) for obj in self.level_matrix[nr][nc]):
            return False

        # Move agent
        self.level_matrix[r][c].remove(agent)
        self.level_matrix[nr][nc].append(agent)
        self.gui.update()  # Update the GUI after the agent moves
        return True

    def move_agent_top(self, agent):
        return self.move_agent(agent, -1, 0)

    def move_agent_bottom(self, agent):
        return self.move_agent(agent, 1, 0)

    def move_agent_left(self, agent):
        return self.move_agent(agent, 0, -1)

    def move_agent_right(self, agent):
        return self.move_agent(agent, 0, 1)

    def remove_agent_from_game(self, agent):
        position = self.find_agent(agent)
        if position is not None:
            r, c = position
            try:
                self.level_matrix[r][c].remove(agent)
                print(f"Agent {agent.name} removed from cell ({r}, {c}).")
            except ValueError:
                print(f"Agent {agent.name} not found in cell ({r}, {c}).")
        else:
            print(f"Agent {agent.name} not found in the matrix.")
        self.gui.update()

    def sabotage(self, agent):
        """
        Versucht, ein angrenzendes Location-Objekt oder das Location-Objekt,
        auf dem der Agent steht, zu sabotieren (damaged = True).

        Nur wenn das Location-Objekt tatsächlich von damaged=False auf damaged=True wechselt,
        wird der Agent in den Cage gesperrt. Anschließend prüfen wir, ob alle Location-Objekte
        inzwischen beschädigt sind. Falls ja, wird die Simulation mit einem Fehler beendet.

        Args:
            agent (AgentConstruct): Der Agent, der sabotieren will.

        Returns:
            bool: True, wenn eine Location gefunden und sabotiert wurde; sonst False.
        """
        position = self.find_agent(agent)
        if position is None:
            return False

        r, c = position
        rows = len(self.level_matrix)
        cols = len(self.level_matrix[0])

        # Alle Nachbarn inklusive der eigenen Zelle
        neighbors = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                for obj in self.level_matrix[nr][nc]:
                    if isinstance(obj, Location):
                        # Nur sabotieren, falls es bisher nicht beschädigt war
                        if not getattr(obj, "damaged", False):
                            obj.damaged = True

                            # Agent in den Cage einsperren
                            self.cage[agent] = agent.actr_time

                            # GUI sofort neu zeichnen (damaged-Overlay anzeigen)
                            self.gui.draw_grid()
                            self.gui.canvas.update_idletasks()
                            self.gui.canvas.update()

                            # Prüfen, ob nach diesem Sabotage-Schritt ALLE Locations beschädigt sind
                            all_damaged = True
                            for row in self.level_matrix:
                                for cell in row:
                                    for element in cell:
                                        if isinstance(element, Location) and not getattr(element, "damaged", False):
                                            all_damaged = False
                                            break
                                    if not all_damaged:
                                        break
                                if not all_damaged:
                                    break

                            if all_damaged:
                                # Wenn wirklich jede Location beschädigt ist, Simulation beenden
                                raise RuntimeError("Game Over - Imposter won")

                            return True
                        # Wenn Location bereits damaged=True ist, ignorieren und weiter suchen
        return False

    def repair(self, agent):
        """
        Versucht, ein angrenzendes Location-Objekt oder das Location-Objekt,
        auf dem der Agent steht, zu reparieren (damaged = False).

        Nur wenn das Location-Objekt tatsächlich von damaged=True auf damaged=False wechselt,
        wird der Agent in den Cage gesperrt.

        Args:
            agent (AgentConstruct): Der Agent, der reparieren will.

        Returns:
            bool: True, wenn eine Location gefunden und repariert wurde; sonst False.
        """
        position = self.find_agent(agent)
        if position is None:
            return False

        r, c = position
        rows = len(self.level_matrix)
        cols = len(self.level_matrix[0])

        # Nachbarn inklusive eigene Zelle
        neighbors = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                for obj in self.level_matrix[nr][nc]:
                    if isinstance(obj, Location):
                        # Nur reparieren, falls es bisher beschädigt war
                        if getattr(obj, "damaged", False):
                            obj.damaged = False
                            # Agent in den Cage für 8 Sekunden einsperren
                            self.cage[agent] = agent.actr_time
                            # GUI sofort neu zeichnen (damaged-Overlay entfernen)
                            self.gui.draw_grid()
                            self.gui.canvas.update_idletasks()
                            self.gui.canvas.update()
                            return True
                        # Wenn bereits damaged=False, ignorieren und weiter suchen
        return False
