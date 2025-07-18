import heapq
import random

import numpy as np
import pyactr as actr

from simulation.LübeckACTR import (
    check_location_damage,
    get_goal,
    get_imaginal,
    production_fired,
    set_goal,
    set_imaginal,
    update_utility,
)


class ChatotAdapter:
    """
    A basic agent, which serves as a demonstrator.

    Attributes:
        agent_construct (str): Nothing
    """

    def __init__(self, agent_construct):
        """
        Args:
            agent_construct: nothing at the moment
        """
        self.agent_construct = agent_construct
        self.colors = {
            "white": "\033[0m",
            "red": "\033[31m",
            "green": "\033[32m",
            "orange": "\033[33m",
            "blue": "\033[34m",
            "purple": "\033[35m",
            "cyan": "\033[36m",
            "lightred": "\033[91m",
            "lightgreen": "\033[92m",
            "yellow": "\033[93m",
            "lightblue": "\033[94m",
            "pink": "\033[95m",
            "lightcyan": "\033[96m",
        }

        self.map_size = 20
        self.los = 3
        self.path = None

        self.last_landmark_x = -1
        self.last_landmark_y = -1
        self.monintor_time = -1

    # Extending ACT-R
    def extending_actr(self):
        """
        Functionality, which extends ACT-R
        In pyactr, ACT-R functionality and regular arithmetic or logical functions are strictly divided.
        The reason for that is a clearer understanding of the agents' behaviour.
        This method will supervise the internal state of the agent.

        Args:
            agent_construct (AgentConstruct): Parent of the SocialAgent
        """
        actr_agent = self.agent_construct.actr_agent
        name = production_fired(self.agent_construct)

        if (
            len(get_goal(actr_agent)) == 0
            or len(get_imaginal(actr_agent, "imaginal")) == 0
        ):
            return

        # Mutable dict versions of the chunks in these buffers
        goal = get_goal_chunk(actr_agent)
        imaginal = get_imaginal_chunk(actr_agent)

        # All of these contain logic that is executed once specific productions are fired.
        # They all take the ACTR agent, name of the fired production, mutable goal chunk and mutable imaginal chunk as arguments.
        # These arguments have been left out of the documentation of the functions to save space.
        self.locate_self(actr_agent, name, goal, imaginal)
        self.choose_landmark(actr_agent, name, goal, imaginal)
        self.handle_emergencies(actr_agent, name, goal, imaginal)
        self.check_target_in_los(actr_agent, name, goal, imaginal)
        self.prepare_direction_decision(actr_agent, name, goal, imaginal)
        self.find_path(actr_agent, name, goal, imaginal)
        self.fetch_path_step(actr_agent, name, goal, imaginal)
        self.move(actr_agent, name, goal, imaginal)
        self.remember_blockade(actr_agent, name, goal, imaginal)
        self.check_agent_nearby(actr_agent, name, goal, imaginal)
        self.monitor_landmark_state(actr_agent, name, goal, imaginal)
        self.monitor_agent_movement(actr_agent, name, goal, imaginal)
        self.prepare_agent_action_decision(actr_agent, name, goal, imaginal)
        self.handle_observations(actr_agent, name, goal, imaginal)

        # Putting the modified chunks back into the buffers
        set_imaginal_chunk(actr_agent, "self", imaginal)
        set_goal_chunk(actr_agent, "goal", goal)

    def locate_self(self, actr_agent, name, goal, imaginal):
        """Saves our agent's position in the imaginal buffer after the 'locate self' production is fired."""
        if name == "locate self":
            for s in self.agent_construct.stimuli[0]:
                stimulus = self.agent_construct.stimuli[0][s]
                if stimulus["text"] == str(imaginal.key):
                    pos = stimulus["position"]
                    imaginal.x = pos[1]
                    imaginal.y = pos[0]
                    self.log("cyan", f"Located agent at {pos[1]}, {pos[0]}!")
                    break

    def choose_landmark(self, actr_agent, name, goal, imaginal):
        """Chooses a landmark that is not the current one and saves its position in the goal buffer after the 'choose landmark' production is fired."""
        if name == "choose landmark":
            usable_decmem = []
            prev_x = -1 if str(goal.x) == "None" else int(str(goal.x))
            prev_y = -1 if str(goal.y) == "None" else int(str(goal.y))
            for d in get_readable_decmem(actr_agent):
                if str(d.isa) == "landmark" and (
                    prev_x != int(str(d.x)) or prev_y != int(str(d.y))
                ):
                    usable_decmem.append(d)
            landmark = random.choice(usable_decmem)
            goal.x = landmark.x
            goal.y = landmark.y
            self.log("cyan", f"Chosen landmark at {goal.x}, {goal.y}!")

    def handle_emergencies(self, actr_agent, name, goal, imaginal):
        """Sets the goal to a damaged landmark if one is spotted. Also decreases trust if a sabotage is spotted while moving."""
        if name == "spotted damaged landmark" or name == "noticed sabotage":
            self.log("red", "EMERGENCY!")
            for s in self.agent_construct.stimuli[0]:
                stimulus = self.agent_construct.stimuli[0][s]
                if stimulus["text"] == "X":
                    pos = stimulus["position"]
                    goal.x = pos[1]
                    goal.y = pos[0]
                    self.log(
                        "cyan",
                        f"Spotted damaged landmark! Updated goal to {goal.x}, {goal.y}.",
                    )
                    break
        if name == "noticed sabotage":
            self.handle_observed_sabotage(goal, imaginal)

    def check_target_in_los(self, actr_agent, name, goal, imaginal):
        """Checks if the target in the goal buffer is in sight and reachable with a path once the corresponding production is fired."""
        if name == "check target in los":
            x = int(str(imaginal.x))
            y = int(str(imaginal.y))
            target_x = int(str(goal.x))
            target_y = int(str(goal.y))
            if x == target_x and y == target_y:
                imaginal.reached = True
                self.log("cyan", "Target already reached!")
            elif max(abs(target_x - x), abs(target_y - y)) <= self.los:
                self.log("cyan", "Target in sight!")
                grid = self.get_search_space(actr_agent, goal, imaginal)
                path = edge_a_star(
                    grid, target_x - x + self.los, target_y - y + self.los, True, True
                )
                if path is None:
                    self.log("red", "... but no path towards it!")
                    imaginal.reached = False
                else:
                    imaginal.reached = True
            else:
                imaginal.reached = False

    def prepare_direction_decision(self, actr_agent, name, goal, imaginal):
        """Updates the utilities of the movement direction productions. This is influenced by the target direction and existing blockades."""
        if name == "prepare direction decision":
            self.log(
                "cyan",
                f"Preparing direction decision towards ({str(goal.x)}, {str(goal.y)})...",
            )
            x = int(str(imaginal.x))
            y = int(str(imaginal.y))
            target_x = int(str(goal.x))
            target_y = int(str(goal.y))
            utility_up = 1.0
            utility_down = 1.0
            utility_left = 1.0
            utility_right = 1.0
            # Consider target direction
            x_magnitude = np.clip(target_x - x, -6, 6) / 6
            y_magnitude = np.clip(target_y - y, -6, 6) / 6
            utility_up += -y_magnitude
            utility_down += y_magnitude
            utility_left += -x_magnitude
            utility_right += x_magnitude
            # Consider blockades
            utility_up += self.get_blockade_influence(actr_agent, x, y, 0, -1)
            utility_down += self.get_blockade_influence(actr_agent, x, y, 0, 1)
            utility_left += self.get_blockade_influence(actr_agent, x, y, -1, 0)
            utility_right += self.get_blockade_influence(actr_agent, x, y, 1, 0)
            # Update utilities
            self.log(
                "cyan",
                f"Updating utilities for up, down, left, right to {utility_up}, {utility_down}, {utility_left}, {utility_right}!",
            )
            update_utility(actr_agent, "choose direction up", utility_up)
            update_utility(actr_agent, "choose direction down", utility_down)
            update_utility(actr_agent, "choose direction left", utility_left)
            update_utility(actr_agent, "choose direction right", utility_right)

    def get_blockade_influence(self, actr_agent, x, y, dir_x, dir_y):
        """Returns the blockade influence in a given direction, which is the value added to the direction movement utility.

        Args:
            actr_agent (ACTRModel): The ACT-R model of our agent
            x (int): The position of our agent
            y (int): The y position of our agent
            dir_x (int): The x component of the direction vector
            dir_y (int): The y component of the direction vector"""
        res = 0.0
        # The direction vector orthogonal to the forward direction
        orthogonal_x = abs(dir_y)
        orthogonal_y = abs(dir_x)
        length = 5
        sideways_length = 2
        for i in range(length):
            # The current position along the path directly in front of our agent in the given main direction
            curr_x = x + dir_x * (i + 1)
            curr_y = y + dir_y * (i + 1)
            for d in get_readable_decmem(actr_agent):
                if str(d.isa) != "blockade":
                    continue
                # The position of the blockade
                dec_x = int(str(d.bx))
                dec_y = int(str(d.by))
                # Checking if the blockade is on the current position on the path or next to it orthogonally
                for dist in range(sideways_length):
                    if (
                        dec_x == curr_x - dist * orthogonal_x
                        and dec_y == curr_y - dist * orthogonal_y
                    ) or (
                        dec_x == curr_x + dist * orthogonal_x
                        and dec_y == curr_y + dist * orthogonal_y
                    ):
                        # Increase negative influence depending on blockade distance from agent, both forward and sideways
                        res -= (
                            1.5
                            * ((length - i) / length)
                            * ((sideways_length - dist) / sideways_length)
                        )
        return res

    def get_search_space(self, actr_agent, goal, imaginal):
        """Returns a 2D array of our agent's field of view. Contains 1 for a blockade and 0 for an empty square."""
        agent_x = int(str(imaginal.x))
        agent_y = int(str(imaginal.y))
        obstacles = []
        for s in self.agent_construct.stimuli[0]:
            stimulus = self.agent_construct.stimuli[0][s]
            if stimulus["text"] == "Z":
                pos = stimulus["position"]
                obstacles.append((int(pos[1]), int(pos[0])))
        grid = []
        for x in range(agent_x - self.los, agent_x + self.los + 1):
            grid.append([])
            for y in range(agent_y - self.los, agent_y + self.los + 1):
                if (x, y) in obstacles:
                    grid[x - agent_x + self.los].append(1)
                elif x < 0 or x >= self.map_size or y < 0 or y >= self.map_size:
                    grid[x - agent_x + self.los].append(1)
                else:
                    grid[x - agent_x + self.los].append(0)
        return grid

    def find_path(self, actr_agent, name, goal, imaginal):
        """Looks for a path and saves it to the imaginal buffer as a list of (x, y) tuples. The tuples have relative coordinates.
        Either looks for a path in the current traversal direction or onto the current landmark."""
        if name == "find path":
            if str(goal.phase) == "traversal":
                direction = str(goal.direction)
                self.log("cyan", f"Looking for path in direction {direction}...")
                grid = self.get_search_space(actr_agent, goal, imaginal)
                target_x = 0
                target_y = 0
                use_y = direction == "up" or direction == "down"
                use_x = not use_y
                if direction == "right":
                    target_x = len(grid) - 1
                if direction == "down":
                    target_y = len(grid) - 1
            elif str(goal.phase) == "landmark":
                self.log("cyan", "Looking for path to landmark...")
                grid = self.get_search_space(actr_agent, goal, imaginal)
                use_x = True
                use_y = True
                target_x = int(str(goal.x)) - int(str(imaginal.x)) + self.los
                target_y = int(str(goal.y)) - int(str(imaginal.y)) + self.los
            # Note: target x and y are relative to the los grid given to the AStar algorithm
            self.path = edge_a_star(grid, target_x, target_y, use_x, use_y)
            if self.path is None:
                self.log("red", "No path found!")
            else:
                self.log("cyan", f"Found path {self.path}!")

    def fetch_path_step(self, actr_agent, name, goal, imaginal):
        """Fetches the direction of the next step in the saved path and saves it in the imaginal buffer. Also saves if the path is finished."""
        if name == "fetch path step":
            if self.path is None:
                goal.path = None
                return
            if len(self.path) == 1:
                goal.path = "finished"
                self.path = None
                return
            curr_x = self.path[0][0]
            curr_y = self.path[0][1]
            next_x = self.path[1][0]
            next_y = self.path[1][1]
            if next_x > curr_x:
                goal.path = "right"
            elif next_x < curr_x:
                goal.path = "left"
            elif next_y > curr_y:
                goal.path = "down"
            elif next_y < curr_y:
                goal.path = "up"
            self.path.pop(0)

    def move(self, actr_agent, name, goal, imaginal):
        """Adjusts the position of our agent in the imaginal after a movement production is fired."""
        if name == "move left":
            imaginal.x = int(str(imaginal.x)) - 1
        if name == "move right":
            imaginal.x = int(str(imaginal.x)) + 1
        if name == "move up":
            imaginal.y = int(str(imaginal.y)) - 1
        if name == "move down":
            imaginal.y = int(str(imaginal.y)) + 1

    def remember_blockade(self, actr_agent, name, goal, imaginal):
        """Adds a blockade chunk to the decmem. Its position is set to one square ahead of the agent in its current direction."""
        if name == "remember blockade":
            dir = str(goal.direction)
            agent_x = int(str(imaginal.x))
            agent_y = int(str(imaginal.y))
            blockade_x = agent_x
            blockade_y = agent_y
            if dir == "up":
                blockade_y -= 1
            if dir == "down":
                blockade_y += 1
            if dir == "left":
                blockade_x -= 1
            if dir == "right":
                blockade_x += 1
            actr_agent.decmem.add(
                actr.chunkstring(string=f"isa blockade bx {blockade_x} by {blockade_y}")
            )

    def check_agent_nearby(self, actr_agent, name, goal, imaginal):
        """Checks if an agent is nearby and adds its key and position to the imaginal if yes. Also saves the current landmark state."""
        if name == "check agent nearby":
            imaginal.lstate = (
                "damaged" if check_location_damage(self.agent_construct) else "intact"
            )
            agents = []
            for s in self.agent_construct.stimuli[0]:
                stimulus = self.agent_construct.stimuli[0][s]
                if stimulus["text"] not in ["X", "Z", str(imaginal.key)]:
                    pos = stimulus["position"]
                    agents.append((stimulus["text"], pos[1], pos[0]))
            if len(agents) == 0:
                imaginal.akey = None
            else:
                key, x, y = random.choice(agents)
                imaginal.akey = key
                imaginal.ax = x
                imaginal.ay = y

    def monitor_landmark_state(self, actr_agent, name, goal, imaginal):
        """Compares the last landmark state to the currently visible one and saves the change (appeared_intact, appeared_damaged, disappeared, repaired, sabotaged) in the imaginal.
        Also updates the current landmark state."""
        if str(goal.monitor_landmark) == "True":
            for s in self.agent_construct.stimuli[0]:
                stimulus = self.agent_construct.stimuli[0][s]
                if stimulus["text"] == "X":
                    pos = stimulus["position"]
                    # This is done to realize when the current landmark exits the FOV and another one enters in the same step
                    if self.last_landmark_x != pos[1] or self.last_landmark_y != pos[0]:
                        imaginal.lstate = None
                    self.last_landmark_x = pos[1]
                    self.last_landmark_y = pos[0]
                    break
            last_state = str(imaginal.lstate)
            check = check_location_damage(self.agent_construct)
            prnt = True
            if check is None:
                curr_state = "None"
            elif check:
                curr_state = "damaged"
            else:
                curr_state = "intact"
            if last_state == "None" and curr_state != "None":
                state_change = "appeared_" + curr_state
            elif curr_state == "None" and last_state != "None":
                state_change = "disappeared"
            elif curr_state == "damaged" and last_state == "intact":
                state_change = "sabotaged"
            elif last_state == "damaged" and curr_state == "intact":
                state_change = "repaired"
            else:
                prnt = False
                state_change = str(imaginal.state_change)
            imaginal.state_change = state_change
            imaginal.lstate = curr_state
            if prnt:
                self.log("green", f"Detected landmark state change: {state_change}")

    def monitor_agent_movement(self, actr_agent, name, goal, imaginal):
        """Compares the last position of the monitored agent to its current one and saves the change in the imaginal buffer (towards, away, gone, still).
        An agent is labeled as still after 3000ms simulation time of no movement."""
        if str(goal.monitor_agent_movement) == "True":
            # Track time when monitoring has started
            if self.monintor_time == -1:
                self.monintor_time = getattr(self.agent_construct, "actr_time", None)
            prev_agent_x = int(str(imaginal.ax))
            prev_agent_y = int(str(imaginal.ay))
            landmark_x = int(str(goal.x))
            landmark_y = int(str(goal.y))
            curr_agent_x = -1
            curr_agent_y = -1
            for s in self.agent_construct.stimuli[0]:
                stimulus = self.agent_construct.stimuli[0][s]
                if stimulus["text"] == str(imaginal.akey):
                    pos = stimulus["position"]
                    curr_agent_x = pos[1]
                    curr_agent_y = pos[0]
                    break
            if curr_agent_x == -1 or curr_agent_y == -1:
                imaginal.agent_movement = "gone"
                self.log("cyan", "Observed agent is gone!")
            elif prev_agent_x == curr_agent_x and prev_agent_y == curr_agent_y:
                # Check if agent hasnt moved for 3000ms
                if (
                    getattr(self.agent_construct, "actr_time", None)
                    - self.monintor_time
                    > 3000
                ):
                    self.log("cyan", "Observed agent appears still.")
                    imaginal.agent_movement = "still"
                    self.monintor_time = getattr(
                        self.agent_construct, "actr_time", None
                    )
            else:
                prev_dist = abs(landmark_x - prev_agent_x) + abs(
                    landmark_y - prev_agent_y
                )
                curr_dist = abs(landmark_x - curr_agent_x) + abs(
                    landmark_y - curr_agent_y
                )
                imaginal.agent_movement = "towards" if curr_dist < prev_dist else "away"
                imaginal.ax = curr_agent_x
                imaginal.ay = curr_agent_y
                self.log(
                    "cyan",
                    f"Observed agent is moving {imaginal.agent_movement} landmark!",
                )
        else:
            self.monintor_time = -1

    def prepare_agent_action_decision(self, actr_agent, name, goal, imaginal):
        """Sets the utilities of the agent action productions (fully trust, ignore, observe, nominate) depending on the trust in the observed agent."""
        if name == "prepare agent action decision":
            akey = str(imaginal.akey)
            trust = int(str(imaginal["trust" + akey])) / 10
            full_trust_utility = trust * 4 - 2.0
            ignore_utility = trust * 2 - 1.0
            observation_utility = 1.0
            nominate_utility = -trust * 4 - 2.0
            self.log(
                "cyan",
                f"Setting agent action utilities for fulltrust, ignore, observe, nominate to: {full_trust_utility}, {ignore_utility}, {observation_utility}, {nominate_utility}.",
            )
            update_utility(actr_agent, "begin agent observation", observation_utility)
            update_utility(actr_agent, "begin nomination", nominate_utility)
            update_utility(actr_agent, "fully trust agent", full_trust_utility)
            update_utility(actr_agent, "ignore agent", ignore_utility)

    def handle_observations(self, actr_agent, name, goal, imaginal):
        """Updates the trust level of the observed agent depending on its movement. In case of an observed repair or sabotage, the trust is devided between the closest agents."""
        if name is not None and name.startswith("observed"):
            akey = str(imaginal.akey)
            trust = int(str(imaginal["trust" + akey]))
            patience = int(str(imaginal.patience))
            if patience > 0:
                imaginal.patience = patience - 1
                self.log("cyan", "Decreasing patience.")
            if name == "observed movement towards damaged landmark":
                trust += 1
                imaginal["trust" + akey] = trust
            elif name == "observed movement away from damaged landmark":
                trust -= 1
                imaginal["trust" + akey] = trust
            elif name == "observed repair":
                self.handle_observed_repair(goal, imaginal)
            elif name == "observed sabotage":
                self.handle_observed_sabotage(goal, imaginal)

    def handle_observed_repair(self, goal, imaginal):
        """Splits a trust increase of 20 between the closest agents."""
        agents = self.get_closest_agents(goal, imaginal)
        if len(agents) == 0:
            self.log("red", "No agents responsible for repair in vision!")
        increase = int(20 / len(agents))
        self.log("cyan", f"Spotted repair by possibly {len(agents)} agents!")
        for key in agents:
            trust = int(str(imaginal["trust" + key]))
            imaginal["trust" + key] = trust + increase
            self.log("cyan", f"Increased trust of {key} by {increase}!")

    def handle_observed_sabotage(self, goal, imaginal):
        """Splits a trust decrease of 20 between the closest agents."""
        agents = self.get_closest_agents(goal, imaginal)
        if len(agents) == 0:
            self.log("red", "No agents responsible for sabotage in vision!")
            return
        decrease = int(20 / len(agents))
        self.log("cyan", f"Spotted sabotage by possibly {len(agents)} agents!")
        for key in agents:
            trust = int(str(imaginal["trust" + key]))
            imaginal["trust" + key] = trust - decrease
            self.log("cyan", f"Decreased trust of {key} by {decrease}!")

    def get_closest_agents(self, goal, imaginal):
        """Returns the closest agents to the currently targeted landmark. Only returns agents that are tied for the closest distance."""
        landmark_x = int(str(goal.x))
        landmark_y = int(str(goal.y))
        agents = []
        min_dist = self.map_size**2
        for s in self.agent_construct.stimuli[0]:
            stimulus = self.agent_construct.stimuli[0][s]
            if stimulus["text"] not in ["X", "Z", str(imaginal.key)]:
                pos = stimulus["position"]
                dist = abs(landmark_x - pos[1]) + abs(landmark_y - pos[0])
                min_dist = min(min_dist, dist)
                agents.append((stimulus["text"], dist))
        keys = []
        for key, dist in agents:
            if dist == min_dist:
                keys.append(key)
        return keys

    def log(self, color, text):
        """Logs a colored message to the console prepended with our agent's name.

        Args:
            color (str): The color of the message, must be part of the list
            text (str): The text to be logged"""
        if self.agent_construct.print_agent_actions:
            print(
                self.colors[color]
                + self.agent_construct.name
                + ", "
                + text
                + self.colors["white"]
            )


class Square:
    """Representation of a square for the AStar algorithm.

    Attributes:
        parent (Square): The parent of the square in a path
        g (int): The g value for the AStar algorithm
        h (int): The h value for the AStar algorithm
        f (int): g + h
        x (int): The x position of the square in the grid
        y (int): The y position of the square in the grid
        blocked (int): 1 if the square is solid, 0 otherwise"""

    def __init__(self, x, y, blocked):
        self.parent = None
        self.g = 10000
        self.h = 0
        self.f = 10000
        self.x = x
        self.y = y
        self.blocked = blocked


def edge_a_star(collision_grid, tx, ty, use_x, use_y):
    """Slightly specialized version of the AStar algorithm. Returns a path from the center of the given grid towards either one edge of the grid or a specific point.

    Args:
        collision_grid (list(list(int))): 2D array of the grid, contains 1 for solid squares and 0 for free squares
        tx (int): The x value of the target
        ty (int): The y value of the target
        use_x (bool): If tx has to be reached to count as having reached the target (False to look for path to a horizontal edge)
        use_y (bool): If ty has to be reached to count as having reached the target (False to look for path to a vertical edge)"""
    closed_list = []
    open_list = []
    # Init Square grid
    grid = []
    for x in range(len(collision_grid)):
        grid.append([])
        for y in range(len(collision_grid)):
            grid[x].append(Square(x, y, collision_grid[x][y]))
    # Init starting square (directly in the middle)
    sx = int(len(collision_grid) / 2)
    sy = sx
    if tx == sx and ty == sy:
        return [(sx, sy)]
    grid[sx][sy].g = 0
    grid[sx][sy].h = 0
    grid[sx][sy].f = 0
    heapq.heappush(open_list, (0.0, sx, sy))
    # Main AStar loop
    while len(open_list) > 0:
        p = heapq.heappop(open_list)
        x = p[1]
        y = p[2]
        closed_list.append((x, y))
        # Iterate over the four neighbours
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx = x + dx
            ny = y + dy
            if (
                nx >= 0
                and nx < len(grid)
                and ny >= 0
                and ny < len(grid)
                and grid[nx][ny].blocked == 0
                and (nx, ny) not in closed_list
            ):
                if (
                    (nx == tx and use_x and not use_y)
                    or (ny == ty and use_y and not use_x)
                    or (nx == tx and ny == ty and use_x and use_y)
                ):
                    grid[nx][ny].parent = grid[x][y]
                    curr_square = grid[nx][ny]
                    path = []
                    while curr_square != grid[sx][sy]:
                        path.append((curr_square.x, curr_square.y))
                        curr_square = curr_square.parent
                    path.append((sx, sy))
                    path.reverse()
                    return path
                else:
                    g_new = grid[x][y].g + 1.0
                    h_new = 0.0
                    if use_y:
                        h_new += abs(ty - ny)
                    if use_x:
                        h_new += abs(tx - nx)
                    f_new = g_new + h_new
                    if grid[nx][ny].f == 10000 or grid[nx][ny].f > f_new:
                        heapq.heappush(open_list, (f_new, nx, ny))
                        grid[nx][ny].f = f_new
                        grid[nx][ny].g = g_new
                        grid[nx][ny].h = h_new
                        grid[nx][ny].parent = grid[x][y]

    return None


# Got this from here: https://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary
# For convenience
class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def get_readable_decmem(actr_agent):
    """Returns all decmem chunks as mutable dicts including their types"""
    result = []
    for d in actr_agent.decmem:
        isa = str(d).split("(")[0]
        m = mutablechunk(d)
        m.isa = isa
        result.append(m)
    return result


def mutablechunk(chunk):
    """Converts a chunk into a mutable dotdict"""
    return dotdict(dict(chunk))


def get_goal_chunk(actr_agent):
    return mutablechunk(get_goal(actr_agent).pop())


def set_goal_chunk(actr_agent, type, chunk):
    set_goal(actr_agent, actr.makechunk(typename=type, **chunk))


def get_imaginal_chunk(actr_agent):
    return mutablechunk(get_imaginal(actr_agent, "imaginal").pop())


def set_imaginal_chunk(actr_agent, type, chunk):
    set_imaginal(actr_agent, actr.makechunk(typename=type, **chunk), "imaginal")
