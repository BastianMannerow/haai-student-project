import random
import math
from simulation.Location import Location
from simulation.Wall import Wall
from simulation.Water import Water
import simulation.LübeckACTR as LübeckACTR

class ImposterAdapter:
    """
    A basic agent, which serves as a demonstrator.

    Attributes:
        agent_construct (AgentConstruct): The ACT-R agent construct.
    """

    def __init__(self, agent_construct):
        self.difficulty = "easy"
        self.cognitive_speed = 0.1  # Minimum time between actions

        # Don't touch this
        self.agent_construct = agent_construct
        self.last_action_time = getattr(agent_construct, 'actr_time', 0)
        self.order = None
        self.target_idx = 0

    def _unwrap(self, cell):
        return cell[0] if isinstance(cell, list) and cell else cell

    def _init_locations(self):
        env = getattr(self.agent_construct, 'middleman', None)
        if not env:
            return
        env = env.experiment_environment
        matrix = env.level_matrix
        locs = []
        for i, row in enumerate(matrix):
            for j, raw in enumerate(row):
                cell = self._unwrap(raw)
                if isinstance(cell, Location):
                    locs.append((i, j))
        if not locs:
            self.order = []
            return
        cx = sum(j for _, j in locs) / len(locs)
        cy = sum(i for i, _ in locs) / len(locs)
        self.order = sorted(
            locs,
            key=lambda p: -math.atan2(p[0] - cy, p[1] - cx)
        )

    def easy(self):
        if self.order is None:
            self._init_locations()
            if not self.order:
                return
        env = self.agent_construct.middleman.experiment_environment
        matrix = env.level_matrix
        r, c = env.find_agent(self.agent_construct)
        tr, tc = self.order[self.target_idx]

        if (r, c) == (tr, tc):
            damage = LübeckACTR.check_location_damage(self.agent_construct)
            if not damage:
                self.agent_construct.middleman.motor_input('I', self.agent_construct)
            self.target_idx = (self.target_idx + 1) % len(self.order)
            return

        next_cell = self._bfs_next((r, c), (tr, tc), matrix)
        if not next_cell:
            self.target_idx = (self.target_idx + 1) % len(self.order)
            return
        nr, nc = next_cell
        dr, dc = nr - r, nc - c
        key = {(1,0): 'S', (-1,0): 'W', (0,1): 'D', (0,-1): 'A'}.get((dr, dc))
        if key is None:
            return
        self.agent_construct.middleman.motor_input(key, self.agent_construct)

    def _bfs_next(self, start, goal, matrix):
        from collections import deque
        visited = set([start])
        queue = deque([(start, None)])
        while queue:
            (r, c), first = queue.popleft()
            for dr, dc in [(-1,0),(0,1),(1,0),(0,-1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < len(matrix) and 0 <= nc < len(matrix[0])):
                    continue
                cell = self._unwrap(matrix[nr][nc])
                if isinstance(cell, (Wall, Water)) or (nr, nc) in visited:
                    continue
                visited.add((nr, nc))
                first_step = first or (nr, nc)
                if (nr, nc) == goal:
                    return first_step
                queue.append(((nr, nc), first_step))
        return None

    def medium(self):
        pass

    def hard(self):
        pass

    def extending_actr(self):
        env = getattr(self.agent_construct, 'middleman', None)
        if not env:
            return
        env = env.experiment_environment
        if hasattr(env, 'cage') and self.agent_construct in env.cage:
            current = getattr(self.agent_construct, 'actr_time', None)
            if current is not None:
                self.last_action_time = current
            return
        current_time = getattr(self.agent_construct, 'actr_time', None)
        if current_time is None or current_time - self.last_action_time < self.cognitive_speed:
            return
        self.last_action_time = current_time
        funcs = {'easy': self.easy, 'medium': self.medium, 'hard': self.hard}
        func = funcs.get(self.difficulty)
        if not func:
            raise ValueError(f"Unknown difficulty: {self.difficulty}")
        func()
