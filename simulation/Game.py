from gui.GUI import MatrixWorldGUI
from simulation.Wall import Wall

class Game:
    """
    The matrix environment.

    Attributes:
        gui (GUI from TK): The gui, which displays the game
    """

    def __init__(self, gui, level_matrix):
        """
        Args:
            gui: displays the game
        """
        self.level_matrix = [[cell if isinstance(cell, list) else [cell] for cell in row] for row in level_matrix]
        self.gui = MatrixWorldGUI(self, gui)
        self.gui.update()
        self.level_matrix = [[cell if isinstance(cell, list) else [cell] for cell in row] for row in level_matrix]

    def find_agent(self, agent):
        for r, row in enumerate(self.level_matrix):
            for c, cell in enumerate(row):
                if agent in cell:
                    return r, c
        return None, None

    def move_agent(self, agent, dr, dc):
        position = self.find_agent(agent)
        if position is None:
            return False

        r, c = position
        nr, nc = r + dr, c + dc

        # Check if new position is within bounds
        if not (0 <= nr < len(self.level_matrix) and 0 <= nc < len(self.level_matrix[0])):
            return False

        # Check if new position contains a wall
        if any(isinstance(obj, Wall) for obj in self.level_matrix[nr][nc]):
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