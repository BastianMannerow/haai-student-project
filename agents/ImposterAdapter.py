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
        self.difficulty = "hard"
        self.cognitive_speed = 0.1  # Minimum time between actions

        # Internal state
        self.agent_construct = agent_construct
        self.last_action_time = getattr(agent_construct, 'actr_time', 0)
        self.order = None            # list of all Location coords
        self.target = None           # for medium/hard

    def _unwrap(self, cell):
        return cell[0] if isinstance(cell, list) and cell else cell

    def _init_locations(self):
        env = getattr(self.agent_construct, 'middleman', None)
        if not env:
            return
        matrix = env.experiment_environment.level_matrix
        locs = []
        for i, row in enumerate(matrix):
            for j, raw in enumerate(row):
                cell = self._unwrap(raw)
                if isinstance(cell, Location):
                    locs.append((i, j))
        self.order = locs

    def _bfs_next(self, start, goal, matrix):
        from collections import deque
        visited = {start}
        queue = deque([(start, None)])
        while queue:
            (r, c), first = queue.popleft()
            for dr, dc in [(-1,0),(0,1),(1,0),(0,-1)]:
                nr, nc = r+dr, c+dc
                if not (0 <= nr < len(matrix) and 0 <= nc < len(matrix[0])):
                    continue
                if (nr, nc) in visited:
                    continue
                cell = self._unwrap(matrix[nr][nc])
                if isinstance(cell, (Wall, Water)):
                    continue
                visited.add((nr, nc))
                step = first or (nr, nc)
                if (nr, nc) == goal:
                    return step
                queue.append(((nr, nc), step))
        return None

    def _get_unsabotaged(self):
        env = self.agent_construct.middleman.experiment_environment
        matrix = env.level_matrix
        return [(i, j) for (i,j) in self.order
                if not getattr(self._unwrap(matrix[i][j]), 'damaged', False)]

    def easy(self):
        if self.order is None:
            self._init_locations()
        unsabotaged = self._get_unsabotaged()
        if not unsabotaged:
            return
        env = self.agent_construct.middleman.experiment_environment
        matrix = env.level_matrix
        r, c = env.find_agent(self.agent_construct)
        # nearest
        tr, tc = min(unsabotaged, key=lambda p: abs(p[0]-r)+abs(p[1]-c))
        if (r, c) == (tr, tc):
            if not LübeckACTR.check_location_damage(self.agent_construct):
                self.agent_construct.middleman.motor_input('I', self.agent_construct)
        else:
            step = self._bfs_next((r,c),(tr,tc),matrix)
            if step:
                dr, dc = step[0]-r, step[1]-c
                key = {(1,0):'S',(-1,0):'W',(0,1):'D',(0,-1):'A'}.get((dr,dc))
                if key:
                    self.agent_construct.middleman.motor_input(key, self.agent_construct)

    def medium(self):
        if self.order is None:
            self._init_locations()
        unsabotaged = self._get_unsabotaged()
        if not unsabotaged:
            return
        env = self.agent_construct.middleman.experiment_environment
        r, c = env.find_agent(self.agent_construct)
        # pick new random if needed
        if self.target not in unsabotaged:
            self.target = random.choice(unsabotaged)
        tr, tc = self.target
        # if at target
        if (r, c) == (tr, tc):
            if not getattr(env, 'cage', {}).get(self.agent_construct):
                if not LübeckACTR.check_location_damage(self.agent_construct):
                    self.agent_construct.middleman.motor_input('I', self.agent_construct)
                self.target = None
            return
        # move
        matrix = env.level_matrix
        step = self._bfs_next((r,c),(tr,tc),matrix)
        if step:
            dr, dc = step[0]-r, step[1]-c
            key = {(1,0):'S',(-1,0):'W',(0,1):'D',(0,-1):'A'}.get((dr,dc))
            if key:
                self.agent_construct.middleman.motor_input(key, self.agent_construct)

    def hard(self):
        if self.order is None:
            self._init_locations()
        unsabotaged = self._get_unsabotaged()
        if not unsabotaged:
            return
        env = self.agent_construct.middleman.experiment_environment
        r, c = env.find_agent(self.agent_construct)
        if self.target not in unsabotaged:
            self.target = random.choice(unsabotaged)
        tr, tc = self.target
        # at target
        if (r, c) == (tr, tc):
            if not getattr(env, 'cage', {}).get(self.agent_construct):
                if not LübeckACTR.agents_in_sight(self.agent_construct):
                    if not LübeckACTR.check_location_damage(self.agent_construct):
                        self.agent_construct.middleman.motor_input('I', self.agent_construct)
                    self.target = None
            return
        # move
        matrix = env.level_matrix
        step = self._bfs_next((r,c),(tr,tc),matrix)
        if step:
            dr, dc = step[0]-r, step[1]-c
            key = {(1,0):'S',(-1,0):'W',(0,1):'D',(0,-1):'A'}.get((dr,dc))
            if key:
                self.agent_construct.middleman.motor_input(key, self.agent_construct)

    def extending_actr(self):
        current_time = getattr(self.agent_construct, 'actr_time', None)
        if current_time is None or current_time - self.last_action_time < self.cognitive_speed:
            return
        self.last_action_time = current_time
        funcs = {'easy': self.easy, 'medium': self.medium, 'hard': self.hard}
        funcs.get(self.difficulty, lambda: (_ for _ in ()).throw(ValueError(f"Unknown difficulty: {self.difficulty}")))()
