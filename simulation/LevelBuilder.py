import random
from collections import deque
from simulation.Food import Food
from simulation.Wall import Wall

def _build_default(height, width, agents, food_amount, wall_density):
    total_cells = height * width
    wall_count = int(total_cells * (wall_density / 100))
    total_objects = len(agents) + food_amount + wall_count
    if total_objects > total_cells:
        raise ValueError("More objects than available cells in the matrix")
    matrix = [[None for _ in range(width)] for _ in range(height)]

    def get_random_empty_position():
        while True:
            row = random.randint(0, height - 1)
            col = random.randint(0, width - 1)
            if matrix[row][col] is None:
                return row, col

    for agent in agents:
        row, col = get_random_empty_position()
        matrix[row][col] = agent
    for _ in range(food_amount):
        row, col = get_random_empty_position()
        matrix[row][col] = Food()
    for _ in range(wall_count):
        row, col = get_random_empty_position()
        matrix[row][col] = Wall()

    if not _are_all_accessible(matrix, agents, height, width):
        raise ValueError("Not all agents and food are accessible")
    return matrix


def _are_all_accessible(matrix, agents, height, width):
    def is_valid(r, c):
        return 0 <= r < height and 0 <= c < width and not isinstance(matrix[r][c], Wall)

    def bfs(start):
        visited = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if is_valid(nr, nc) and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return visited

    positions = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if isinstance(matrix[r][c], (Food, type(agents[0])))
    ]
    if not positions:
        return True
    accessible_positions = bfs(positions[0])
    return all(pos in accessible_positions for pos in positions)


def build_perception_and_action_1(height, width, agents, food_amount, wall_density):
    if len(agents) != 1:
        raise ValueError("Perception & Action 1 requires exactly one agent")
    size = 5
    matrix = [[None for _ in range(size)] for _ in range(size)]
    center = size // 2
    matrix[center][center] = agents[0]
    available = [(r, c) for r in range(size) for c in range(size) if (r, c) != (center, center)]
    for r, c in random.sample(available, 3):
        matrix[r][c] = Food()
    return matrix


def build_perception_and_action_2(height, width, agents, food_amount, wall_density):
    if len(agents) != 1:
        raise ValueError("Perception & Action 2 requires exactly one agent")
    size = 5
    matrix = [[None for _ in range(size)] for _ in range(size)]
    center = size // 2
    matrix[center][center] = agents[0]
    fixed_positions = [(0, 0), (0, 4), (4, 0)]
    for r, c in fixed_positions:
        matrix[r][c] = Food()
    return matrix


def build_perception_and_action_3(height, width, agents, food_amount, wall_density):
    if len(agents) != 2:
        raise ValueError("Perception & Action 3 requires exactly two agents")
    h, w = 2, 10
    matrix = [[None for _ in range(w)] for _ in range(h)]
    left_agent = next((a for a in agents if a.name != 'Bibor'), None)
    beedrill = next((a for a in agents if a.name == 'Bibor'), None)
    if not left_agent or not beedrill:
        raise ValueError("Agents must include one named 'Beedrill' and one other for PA 3")
    matrix[1][0] = left_agent
    matrix[1][1] = beedrill
    return matrix


def build_chunks_1(height, width, agents, food_amount, wall_density):
    # Spielfeld 1 hoch, 2 breit
    matrix = [[None for _ in range(2)] for _ in range(1)]
    glumanda = next((a for a in agents if a.name == 'Glumanda'), None)
    sarzenia = next((a for a in agents if a.name == 'Sarzenia'), None)
    individual_agent = next((a for a in agents if a.name not in ('Glumanda', 'Sarzenia')), None)
    if glumanda is None or sarzenia is None or individual_agent is None:
        raise ValueError("Agents list must contain instances of Glumanda, Sarzenia, and your individual agent")
    matrix[0][0] = individual_agent
    # benutze vorhandene Agent-Instanzen, nicht erneut konstruieren
    matrix[0][1] = random.choice([glumanda, sarzenia])
    if matrix[0][1] is glumanda:
        glumanda.middleman.simulation.agent_list.remove(sarzenia)
    else:
        glumanda.middleman.simulation.agent_list.remove(glumanda)
    return matrix


def build_chunks_2(height, width, agents, food_amount, wall_density):
    size = 3
    matrix = [[None for _ in range(size)] for _ in range(size)]
    pinsir_proto = next((a for a in agents if a.name == 'Pinsir'), None)
    other = next((a for a in agents if a.name != 'Pinsir'), None)
    if pinsir_proto is None or other is None:
        raise ValueError("Agents list must contain at least one Pinsir and at least one other agent")
    center = size // 2
    matrix[center][center] = other
    count_pinsir = random.randint(1, 5)
    positions = [(r, c) for r in range(size) for c in range(size) if (r, c) != (center, center)]
    for r, c in random.sample(positions, count_pinsir):
        matrix[r][c] = pinsir_proto
    return matrix


def build_utility_reinforcement_learning_1(height, width, agents, food_amount, wall_density):
    size = 3
    matrix = [[None for _ in range(size)] for _ in range(size)]
    deoxys_proto = next((a for a in agents if a.name == 'Deoxys'), None)
    center_agent = next((a for a in agents if a.name != 'Deoxys'), None)
    if deoxys_proto is None or center_agent is None:
        raise ValueError("Agents list must contain at least one Deoxys and at least one non-Deoxys agent")
    center = size // 2
    matrix[center][center] = center_agent
    dirs = {
        (0, center): 0.50,
        (size-1, center): 0.25,
        (center, 0): 0.75,
        (center, size-1): 1.00
    }
    for (r, c), food_prob in dirs.items():
        if random.random() < food_prob:
            matrix[r][c] = Food()
        else:
            matrix[r][c] = deoxys_proto
    if deoxys_proto is None:
        deoxys_proto.middleman.simulation.agent_list.remove(deoxys_proto)
    return matrix


def build_utility_reinforcement_learning_2(height, width, agents, food_amount, wall_density):
    h, w = 13, 3
    matrix = [[None for _ in range(w)] for _ in range(h)]
    darkrai_proto = next((a for a in agents if a.name == 'Darkrai'), None)
    glumanda_proto = next((a for a in agents if a.name == 'Glumanda'), None)
    center_agent = next((a for a in agents if a.name != 'Darkrai'), None)
    if darkrai_proto is None or glumanda_proto is None or center_agent is None:
        raise ValueError("Agents list must contain Darkrai, Glumanda, and at least one other agent")
    mid_row = h // 2
    matrix[mid_row][w // 2] = center_agent
    if random.random() < 0.5:
        matrix[0][w // 2] = darkrai_proto
        matrix[h-1][w // 2] = glumanda_proto
    else:
        matrix[0][w // 2] = glumanda_proto
        matrix[h-1][w // 2] = darkrai_proto
    return matrix


def build_utility_reinforcement_learning_3(height, width, agents, food_amount, wall_density):
    return _build_default(height, width, agents, food_amount, wall_density)


def build_affect_deduction_paralogism_1(height, width, agents, food_amount, wall_density):
    return _build_default(height, width, agents, food_amount, wall_density)


def build_affect_deduction_paralogism_2(height, width, agents, food_amount, wall_density):
    return _build_default(height, width, agents, food_amount, wall_density)


def build_affect_deduction_paralogism_3(height, width, agents, food_amount, wall_density):
    return _build_default(height, width, agents, food_amount, wall_density)


def build_level(height, width, agents, food_amount, wall_density, level_type=None):
    presets = {
        'Perception & Action 1': build_perception_and_action_1,
        'Perception & Action 2': build_perception_and_action_2,
        'Perception & Action 3': build_perception_and_action_3,
        'Chunks 1': build_chunks_1,
        'Chunks 2': build_chunks_2,
        'Utility 1': build_utility_reinforcement_learning_1,
        'Utility 2': build_utility_reinforcement_learning_2,
        'Affect, Deduction & Paralogism 1': build_affect_deduction_paralogism_1,
        'Affect, Deduction & Paralogism 2': build_affect_deduction_paralogism_2,
        'Affect, Deduction & Paralogism 3': build_affect_deduction_paralogism_3,
    }
    if level_type is None:
        return _build_default(height, width, agents, food_amount, wall_density)
    if level_type in presets:
        return presets[level_type](height, width, agents, food_amount, wall_density)
    raise ValueError("Unknown level type")
