import pyactr as actr


class Hoothoot:
    """
    A basic agent, which serves as a demonstrator.

    Attributes:
        this_agent_key (str): Self identification from AgentConstruct agent_dictionary
        other_agents_key_list (list): Identification from AgentConstruct agent_dictionary for other agents but self
        environ (Environment): pyactr environment
        actr_agent (ACTRModel): pyactr agent
        goal_phases (list): All goal states, which are independent of each other. Makes code more readable
        initial_goal (Chunk): If the agent crashes, it will start again with this goal
    """

    def __init__(self, environ):
        """
        Args:
            environ: pyactr environment (can be overwritten later)
        """
        self.this_agent_key = None
        self.other_agents_key_list = None

        self.environ = environ
        self.actr_agent = actr.ACTRModel(environment=self.environ, motor_prepared=True, automatic_visual_search=True,
                                         subsymbolic=True)
        self.decmem = self.actr_agent.decmem

        #self.goals.append("imaginal")
        # add task goal
        self.goal_phases= ["decide", "walk", "guard"]
        self.initial_goal = actr.chunkstring(string=f"""
        isa     decide
        state   inconclusive
        """)

    # Building the agent
    def build_agent(self, agent_list):
        """
        Builds an ACT-R agent

        Args:
            agent_list (list): Strings from the AgentConstruct dictionary to identify other agents

        Returns:
            pyactr.ACTRAgent: The final actr_agent object from pyactr
        """
        self.this_agent_key = agent_list[0]
        self.other_agents_key_list = agent_list[1:]

        # ACT-R configuration for this agent
        actr_agent = self.actr_agent
        actr_agent.model_parameters[
            "utility_noise"] = 0  # 0.0 = only base utility
        actr_agent.model_parameters["baselevel_learning"] = False


        #### GOAL CHUNK TYPES

        goal_phases = self.goal_phases
        for phase in goal_phases:
            actr.chunktype(phase, "state")
        

        #### LOCATIONS

        actr.chunktype("landmark",("name", "posx", "posy", "state"))
        locations = {"Uni": (18, 16), "Blauer_Engel": (2,15), "Holstentor": (8,7), "MUK": (1, 2)
                     , "Hauptbahnhof": (8, 1), "Draeger": (17, 2), "Perfect_Spot": (4, 5)}
        STATES = ["intact", "kaputt", "unknown"]
        for name, position in locations.items():
            self.decmem.add(actr.chunkstring(string=f"""
                isa landmark
                name {name}
                posx {str(position[0])}
                posy {str(position[1])}
                state {STATES[0]}"""))

        #### WAYPOINTS

        actr.chunktype("waypoint", ("landmark posx posy nextx nexty up down left right"))

        #### POKEMON

        actr.chunktype("pokemon", "name lastknownx lastknowny suspicion")

        # Navigation Cunks
        actr.chunktype("walk_somewhere","location destination")
        actr.chunktype("obstacle", "location evade_direction")
        actr.chunktype("destination", "name posx posy")
        
        # Agent Model
        #for phase in goal_phases:
        #    self.add_productions(actr_agent, phase)

        self.declare_imaginals(actr_agent)
        self.add_productions_destination(actr_agent, locations)
        self.add_productions_walking(actr_agent)
        return actr_agent

    def declare_imaginals(self, actr_agent):
        actr_agent.set_goal(name="destination", delay = 0)

    def add_productions(self, actr_agent, phase):
        actr_agent.productionstring(name=f"count {phase}", string=f"""
                =g>
                isa     {phase}
                state   {phase}Start
                ==>
                =g>
                isa     {phase}
                state   {phase}Start""")
        
    def add_productions_destination(self, actr_agent, destinations):
        for destination in destinations:
            actr_agent.productionstring(name=f"thinking of going to {destination}", string=f"""
                    =g>
                    isa decide
                    state inconclusive
                    ==>
                    =g>
                    isa decide
                    state conclusive
                    +retrieval>
                    name {destination}
                    """, utility = 30)
            actr_agent.productionstring(name=f"definitely going to {destination}", string=f"""
                    =g>
                    isa decide
                    state conclusive
                    ?retrieval>
                    buffer full
                    =retrieval>
                    isa landmark
                    name {destination}
                    posx =x
                    posy =y
                    ==>
                    =g>
                    isa walk
                    state wait
                    +destination>
                    isa destination
                    name {destination}
                    posx =x
                    posy =y    
                    """)
            
    def add_productions_walking(self, actr_agent):
        directions = ["W", "A", "S", "D"]
        for key in directions:
            actr_agent.productionstring(name=f"walk {key}", string=f"""
                        =g>
                        isa walk
                        state walk_{key}
                        ==>
                        =g>
                        isa walk
                        state wait
                        +manual>
                        isa _manual
                        cmd press_key
                        key {key}
                """, utility = 10)
            
    def add_productions_waypoints(self, actr_agent):
        pass

    def add_productions_observation(self, actr_agent):
        actr_agent.productionstring(name=f"Observing Landmark", string=f"""
                    =g>
                    isa guard
                    state observe
                    ==>
                    =g>
                    isa guard
                    state observe
                    """, utility = 80)
        actr_agent.productionstring(name=f"Enough Observing", string=f"""
                   =g>
                    isa guard
                    state observe
                    ==>
                    =g>
                    isa decide
                    state inconclusive
                    """, utility = 10)
        
