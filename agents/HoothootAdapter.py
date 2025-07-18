from simulation import LübeckACTR
import pyactr as actr

import pyactr


class HoothootAdapter:
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
        self.last_direction = (0, 0)
        self.directions = {(1,0):'S',(-1,0):'W',(0,1):'D',(0,-1):'A'}
        self.observation_targets = {}
        self.pokemon = {}
        self.obsersavtion_position = (4,5)
        self.path = []
        self.destination_waypoints={}
        self.destination = None

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
        
        #LübeckACTR.set_imaginal(actr_agent, actr.chunkstring(string=f"isa position posx 2 posy 2"), "selfknowledge")

        #production = LübeckACTR.production_fired(self.agent_construct)
        #print("Following Production has Fired: ", production)
        goal = LübeckACTR.get_goal(actr_agent)._data
        LübeckACTR.update_utility(actr_agent, "thinking of going to Perfect_Spot", 200)
        if goal:
            goal = list(goal.copy())[0]

            if goal.typename == "guard":
                # Visual Stimuli
                position, obstacles, landmark, agents = self.lookaround()
                #be aware, if someone is nearby
                self.observation_targets = {}
                if agents:
                    for agent in agents:
                        agent_name = agent["text"]
                        agent_position = agent["position"]
                        if agent_name in self.pokemon:
                            pokemon = self.pokemon[agent_name]
                            pokemon["last_position"] = pokemon["position"]
                            pokemon["position"] = agent_position

                        else:
                            self.pokemon[agent_name] = {"position": agent_position, "last_position": agent_position, "suspicion": 0, "possible_sabotage": False, "possible_repair": False}
                        if landmark:
                            self.observation_targets[agent_name] = self.pokemon[agent_name]
                self.observe(position, landmark, agents)

            elif goal.typename == "walk" and str(goal.__getattr__("state")) == "walk":
                utilities = []
                for direction in self.directions.keys():
                    utilities.append(actr_agent.productions[f"walk {self.directions[direction]}"].utility)

                pass
            elif goal.typename == "walk": #and str(goal.__getattr__("state")) == "wait":
                
                destination = list(actr_agent.retrieval._data.copy())[0]
                destination_name = str(destination.__getattr__("name"))
                destination = (int(str(destination.__getattr__("posx"))), int(str(destination.__getattr__("posy"))))
                self.destination_waypoints.setdefault(destination_name, [destination])
                self.destination = destination
                # Visual Stimuli
                position, obstacles, landmark, agents = self.lookaround()
                # Set next Target
                if self.destination_waypoints[destination_name]:
                    current_waypoints = self.destination_waypoints[destination_name].copy()
                    waypoint = min(current_waypoints, key=lambda m: self.manhattan_distance(m, position))

                    waypoint_idx = current_waypoints.index(waypoint)
                    if self.manhattan_distance(waypoint, position) == 0 and waypoint_idx != 0:
                        current_waypoints.pop(waypoint_idx)
                        waypoint = min(current_waypoints, key=lambda m: self.manhattan_distance(m, position))


                # Logic For Going To Destination
                if position != self.destination:
                    self.move_step(actr_agent, position, waypoint, obstacles) 
                    # Trace Path
                    if self.path:
                        if self.path[-1] != position:
                            self.path.append(position)
                    else:
                        self.path.append(position)  

                else:
                    # Update Waypoint and Path List
                    waypoints = self.generate_waypoints(self.path)
                    waypoints = waypoints + self.destination_waypoints[destination_name]
                    waypoints.sort()
                    self.destination_waypoints[destination_name] = self.filter_waypoints(waypoints)
                    self.path = []

                    if landmark:
                        if not LübeckACTR.check_location_damage(self.agent_construct):
                            LübeckACTR.set_goal(actr_agent, actr.chunkstring(string=f"isa guard state observe"))

                        self.observe(position, landmark, agents)
                        
                    if position == landmark and LübeckACTR.check_location_damage(self.agent_construct):
                        self.agent_construct.middleman.motor_input("R", self.agent_construct)

    def lookaround(self):
        #print("Hoothoot looks around if it sees something interesting")
        stimuli = self.agent_construct.stimuli
        obstacles = []
        agents = []
        landmarks = []
        for (key, stimulus) in stimuli[0].items():
                    if stimulus["text"] == "A":
                        position = stimulus["position"]
                    elif stimulus["text"] == "Z":
                        obstacles.append(stimulus["position"])
                    elif stimulus["text"] == "X":
                        landmarks.append(stimulus["position"])
                    else:
                        agents.append(stimulus)

        return position, obstacles, landmarks, agents

    def observe(self, position, landmarks, agents):
        
        # Check for suspicious behavior
        for name, target in self.observation_targets.items():
            for landmark in landmarks:
                   # bigger than zero means towards
                    distance_change = (self.manhattan_distance(target["last_position"], landmark) 
                                        - self.manhattan_distance(target["position"], landmark) )
                          
                    if LübeckACTR.check_location_damage(self.agent_construct):
                        # if location is damaged suspicion is reversed
                        distance_change *= -1
                        # this means target was caught red-handed
                        if target["possible_sabotage"]:
                            target["suspicion"] += 150
                    else:
                        if target["possible_repair"]:
                            target["suspicion"] -= 150

                    # Suspicion from going to and from landmarks
                    if distance_change > 0:
                        target["suspicion"] += 2
                    elif distance_change < 0:
                        target["suspicion"] -= 2


                    if target["position"] == landmark:
                        if LübeckACTR.check_location_damage(self.agent_construct):
                            target["possible_repair"] = True
                            if distance_change == 0:
                                target["suspicion"] -= 5
                        else: 
                            target["possible_sabotage"] = True
                            if distance_change == 0:
                                target["suspicion"] += 5

                    else:
                        target["possible_sabotage"] = False
                        target["possible_repair"] = False
            
            if target["suspicion"] >= 100:
                self.agent_construct.middleman.motor_input("N", self.agent_construct)
                self.agent_construct.middleman.motor_input(name, self.agent_construct)

            if target["suspicion"] > 0:
                target["suspicion"] = 0

            self.pokemon[name] = target

            
    def move_step(self, actr_agent, position, destination, obstacles = []):
         # Get Direction
        dir, possible_dirs, last_dir = self.decide_direction(position, destination, obstacles)
        key = self.directions.get(dir)    
        self.agent_construct.middleman.motor_input(key, self.agent_construct)
        print(f"Hoothoot is walking in {key} direction")
        #LübeckACTR.set_goal(actr_agent, actr.chunkstring(string=f"isa walk state walk_{key}"))
        
        # everything to 0
        #for direction in self.directions.keys():
        #    actr_agent.productions[f"walk {self.directions[direction]}"].utility = 0

        # possible to 10
        #for direction in possible_dirs:
        #    actr_agent.productions[f"walk {self.directions[direction]}"].utility = 20
        
        # best way to 80
        #actr_agent.productions[f"walk {self.directions[dir]}"].utility = 80

        # best and already used way to 120
        #if last_dir:
        #    actr_agent.productions[f"walk {self.directions[last_dir]}"].utility = 150


    def decide_direction(self, agent_pos, target, obstacles):

        moves = [(agent_pos[0] + dir[0], agent_pos[1] + dir[1]) for dir, key in self.directions.items()]
        moves = [m for m in moves if 0 <= m[0] <= 19 and 0 <= m[1] <= 19]
        
        moves = list(set(moves) - set(obstacles))
        
        last_move = (agent_pos[0] + self.last_direction[0], agent_pos[1] + self.last_direction[1])
        last_positon = (agent_pos[0] - self.last_direction[0], agent_pos[1] - self.last_direction[1])

        if len(moves) > 1 and last_positon in moves:
            moves.remove(last_positon)

        best_move = min(moves, key=lambda m: self.manhattan_distance(m, target))
        
        last_dir = None
        if self.manhattan_distance(best_move, target) >= self.manhattan_distance(last_move, target) and last_move in moves:
            best_move = last_move
            #last_dir = self.last_direction

        possible_dirs = [(move[0]- agent_pos[0], move[1] - agent_pos[1]) for move in moves]
        best_dir = (best_move[0] - agent_pos[0], best_move[1] - agent_pos[1])  
        self.last_direction = best_dir
        return best_dir, possible_dirs, last_dir
        
    def manhattan_distance(self, position, destination):
        return abs(position[0]-destination[0]) + abs(position[1]-destination[1])
    
    def path_derivative(self, path):
        derivatives = []
        for i in range(len(path)-1):
            x0, y0 = path[i]
            x1, y1 = path[i+1]
            dx = x1 - x0
            dy = y1 - y0
            derivatives.append((dx, dy))
        return derivatives

    def generate_waypoints(self, path):

        pos_to_index = {}
        path_without_loop = []

        for i, pos in enumerate(path):
            if pos in pos_to_index:
                # Found a loop: cut out positions between pos_to_index[pos]+1 and i (inclusive)
                loop_start = pos_to_index[pos]
                # Remove loop: keep path up to loop_start, then continue from i+1
                path_without_loop = path_without_loop[:loop_start+1]
                # Reset pos_to_index to match new result
                pos_to_index = {p: idx for idx, p in enumerate(path_without_loop)}
            else:
                path_without_loop.append(pos)
                pos_to_index[pos] = len(path_without_loop)-1

        ## generate waypoints from derivatives
        derivatives = self.path_derivative(path_without_loop)
        waypoints = []
        clean_path = []
        clean_path.append(path_without_loop[0])
        result = [derivatives[0]]
        clean_path.append(tuple(x + y for x, y in zip(clean_path[-1], result[-1])))

        for item in derivatives[1:]:
            if item != result[-1]:
                result.append(item)
                waypoints.append(clean_path[-1])
            clean_path.append(tuple(x + y for x, y in zip(clean_path[-1], item)))

        # waypoint filter
        return self.filter_waypoints(waypoints)

    def filter_waypoints(self, waypoints):
        filtered = [waypoints[0]]
        for point in waypoints[1:]:
            last_kept = filtered[-1]
            dx = point[0] - last_kept[0]
            dy = point[1] - last_kept[1]
            if dx + dy >= 3:
                filtered.append(point)

        return filtered
                    