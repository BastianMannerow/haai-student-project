import random
from collections import deque
from simulation.Food import Food
from simulation.Wall import Wall
from simulation.Water import Water
from simulation.Location import Location

def _build_default(height, width, agents, food_amount, wall_density):
    total_cells = height * width
    wall_count = int(total_cells * (wall_density / 100))
    total_objects = len(agents) + food_amount + wall_count
    if total_objects > total_cells:
        raise ValueError("Mehr Objekte als verfügbare Zellen in der Matrix")
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
        raise ValueError("Nicht alle Agenten und Nahrung sind erreichbar")
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
        raise ValueError("Perception & Action 1 benötigt genau einen Agenten")
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
        raise ValueError("Perception & Action 2 benötigt genau einen Agenten")
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
        raise ValueError("Perception & Action 3 benötigt genau zwei Agenten")
    h, w = 2, 10
    matrix = [[None for _ in range(w)] for _ in range(h)]
    left_agent = next((a for a in agents if a.name != 'Bibor'), None)
    beedrill = next((a for a in agents if a.name == 'Bibor'), None)
    if not left_agent or not beedrill:
        raise ValueError("Agents müssen einen mit dem Namen 'Bibor' und einen anderen enthalten für PA 3")
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
        raise ValueError("Agents-Liste muss Instanzen von Glumanda, Sarzenia und einem weiteren Agenten enthalten")
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
        raise ValueError("Agents-Liste muss mindestens einen Pinsir und einen weiteren Agenten enthalten")
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
        raise ValueError("Agents-Liste muss mindestens einen Deoxys und einen Nicht-Deoxys-Agenten enthalten")
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
        raise ValueError("Agents-Liste muss Darkrai, Glumanda und mindestens einen weiteren Agenten enthalten")
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


def build_agent_project(height, width, agents, food_amount, wall_density):
    """
    Neues Level: 'Agent Project'
    - Fehlermeldung, wenn kein Agent mit name == 'Imposter' vorhanden ist.
    - Fehlermeldung, wenn kein weiterer Agent (außer Imposter) vorhanden ist.
    - Feste Kartenstruktur mit Z für Wall, W für Water, X für Location.
    - Alle Agenten werden in zulässige, freie Zellen unten rechts gesetzt.
    """

    # 1. Prüfen: Mindestens ein 'Imposter' und mindestens ein anderer Agent
    imposter = next((a for a in agents if a.name == 'Imposter'), None)
    #if imposter is None:
    #    raise ValueError("Für 'Agent Project' muss mindestens ein Agent mit dem Namen 'Imposter' existieren.")
    others = [a for a in agents if a.name != 'Imposter']
    if len(others) < 1:
        raise ValueError("Für 'Agent Project' muss es mindestens einen weiteren Agenten neben 'Imposter' geben.")

    # 2. Feste Karte als mehrzeiliger String (Semikolons trennen Zellen)
    map_str = [
        "Z;;;;;;W;;;;;;;;;;;;;W",
        "Z;;X;;;;;W;;;;;;;;;;;;W",
        "Z;;;;;;;;;;;;;;;X;;;;W",
        "W;;;;;;;;;W;;;;;;;;;;W",
        ";W;;;;;;;;Z;W;;;;;;;;;W",
        ";;W;;;;;;;;Z;W;;;;;;;;W",
        ";;;W;;;;;;;;W;;;;;;;;W",
        ";;;;W;;;;X;;;;;;;;;;;W",
        ";X;;;;;;;;;;W;;;;;;;W;W",
        ";;;;W;;;;;;;W;;;;;;;W;Z",
        ";;;;;W;Z;Z;Z;;Z;W;;;;;;;;",
        ";;;;;;W;W;Z;;W;;W;W;W;W;W;W;W;",
        ";;;;;;;W;Z;;W;;;Z;Z;Z;Z;Z;Z;",
        ";Z;Z;Z;Z;;;W;W;;W;;;Z;;;;;Z;",
        ";;;;;;;;;;;;;;;;;;",
        ";;;;;;;W;;;;W;Z;Z;;;;;;",
        ";;;;;;;W;;Z;;W;Z;Z;;;;;;Z",
        ";;X;;;;;W;;;;W;Z;Z;;;;;Z;Z",
        ";;;;;;;W;;;;W;Z;Z;;;X;;Z;Z",
        "Z;Z;Z;Z;Z;Z;Z;Z;W;W;W;W;Z;Z;;;;;Z;Z"
    ]

    # 3. Jede Zeile splitten, um Zellen zu bestimmen; maximale Breite ermitteln
    rows = [row.split(';') for row in map_str]
    max_width = max(len(cells) for cells in rows)

    # 4. Matrix initialisieren (Höhe = Anzahl Zeilen, Breite = max_width)
    H = len(rows)
    W = max_width
    matrix = [[None for _ in range(W)] for _ in range(H)]

    # 5. Map-Zeichen in Objekte übersetzen
    for r, cells in enumerate(rows):
        # Wenn diese Zeile kürzer als max_width, mit leeren Zellen auffüllen
        if len(cells) < max_width:
            cells = cells + [''] * (max_width - len(cells))
        for c, cell in enumerate(cells):
            if cell == 'Z':
                matrix[r][c] = Wall()
            elif cell == 'W':
                matrix[r][c] = Water()
            elif cell == 'X':
                matrix[r][c] = Location()
            else:
                matrix[r][c] = None

    # 6. Alle Agenten in freie Zellen "unten rechts" packen
    #    Wir gehen rückwärts über die Matrix und füllen freie Zellen,
    #    bis alle Agenten platziert sind.
    remaining_agents = agents.copy()
    for r in range(H - 1, -1, -1):
        for c in range(W - 1, -1, -1):
            if not remaining_agents:
                break
            if matrix[r][c] is None:
                matrix[r][c] = remaining_agents.pop(0)
        if not remaining_agents:
            break

    # Falls nach diesem Prozess noch Agenten übrig sind,
    # bedeutet dies: keine ausreichenden leeren Felder (sollte aber bei dieser Karte selten auftreten).
    if remaining_agents:
        raise ValueError("Nicht genügend freie Zellen, um alle Agenten unten rechts zu platzieren.")

    return matrix


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
        'Agent Project': build_agent_project,  # Neu hinzugefügt
    }
    if level_type is None:
        return _build_default(height, width, agents, food_amount, wall_density)
    if level_type in presets:
        return presets[level_type](height, width, agents, food_amount, wall_density)
    raise ValueError("Unbekannter Level-Typ: {}".format(level_type))
