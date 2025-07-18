import pyactr as actr

MAPSIZE = 20


class Chatot:
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
        self.actr_agent = actr.ACTRModel(
            environment=self.environ,
            motor_prepared=True,
            automatic_visual_search=False,
            subsymbolic=True,
        )

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
        # 0.0 = only base utility
        actr_agent.model_parameters["utility_noise"] = 0.35
        actr_agent.model_parameters["baselevel_learning"] = False

        # Goal Chunk Type
        actr.chunktype(
            "goal",
            "phase state x y direction path monitor_landmark monitor_agent_movement",
        )

        # Imaginal Chunk Type
        actr.chunktype(
            "self",
            "key x y lstate state_change akey ax ay agent_movement reached patience "
            + " ".join(["trust" + key for key in self.other_agents_key_list]),
        )

        # Decmem Chunk Types
        actr.chunktype("landmark", "x y")
        actr.chunktype("blockade", "bx by")

        self.initial_goal = actr.chunkstring(
            string="""
                isa goal
				phase init
                state init
            """
        )

        actr_agent.set_goal(name="imaginal", delay=0)

        landmarks = [
            (1, 2),
            (2, 15),
            (7, 8),
            (8, 1),
            (17, 2),
            (18, 16),
        ]  # in (y, x) format
        for landmark in landmarks:
            actr_agent.decmem.add(
                actr.chunkstring(string=f"isa landmark x {landmark[1]} y {landmark[0]}")
            )

        # Agent Model
        self.add_init_productions(actr_agent)
        self.add_traversal_productions(actr_agent)
        self.add_pathfinding_productions(actr_agent)
        self.add_landmark_productions(actr_agent)
        self.add_observation_productions(actr_agent)
        return actr_agent

    def add_init_productions(self, actr_agent):
        """Adds productions that initialize the buffers and the imaginal state"""
        actr_agent.productionstring(
            name="init",
            string=f"""
            =g>
            isa goal
            phase init
            state init
            ==>
            =g>
            isa goal
            phase init
            state locate_self
            monitor_landmark True
            +imaginal>
            isa self
            key {self.this_agent_key}
            {"\n".join(["trust" + key + " 0" for key in self.other_agents_key_list])}
            """,
        )
        actr_agent.productionstring(
            name="locate self",
            string="""
            =g>
            isa goal
            phase init
            state locate_self
            ==>
            =g>
            isa goal
			phase traversal
            state choose_landmark
            """,
        )

    def add_traversal_productions(self, actr_agent):
        """Adds productions for the traversal phase, which means picking a landmark as a goal and moving towards it"""
        # Target choosing
        actr_agent.productionstring(
            name="choose landmark",
            string="""
            =g>
            isa goal
			phase traversal
            state choose_landmark
            ==>
            =g>
            isa goal
			phase traversal
            state check_for_emergencies
            """,
        )

        # Emergency checking and handling
        actr_agent.productionstring(
            name="no emergency",
            string="""
            =g>
            isa goal
			phase traversal
            state check_for_emergencies
            ==>
            =g>
            isa goal
			phase traversal
            state check_target_in_los
            """,
        )
        actr_agent.productionstring(
            name="spotted damaged landmark",
            string="""
            =g>
            isa goal
			phase traversal
            state check_for_emergencies
            =imaginal>
            isa self
            state_change appeared_damaged
            ==>
            =g>
            isa goal
			phase landmark
            state check_agent_nearby
            =imaginal>
            isa self
            state_change None
            """,
            utility=100,
        )
        actr_agent.productionstring(
            name="noticed sabotage",
            string="""
            =g>
            isa goal
			phase traversal
            state check_for_emergencies
            =imaginal>
            isa self
            state_change sabotaged
            ==>
            =g>
            isa goal
			phase landmark
            state check_agent_nearby
            =imaginal>
            isa self
            state_change None
            """,
            utility=100,
        )

        # Target checks
        actr_agent.productionstring(
            name="check target in los",
            string="""
            =g>
            isa goal
			phase traversal
            state check_target_in_los
            ==>
            =g>
            isa goal
			phase traversal
            state process_target_check
            """,
        )
        actr_agent.productionstring(
            name="target not reached",
            string="""
            =g>
            isa goal
			phase traversal
            state process_target_check
            =imaginal>
            isa self
            reached False
            ==>
            =g>
            isa goal
			phase traversal
            state prepare_direction_decision
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="target reached",
            string="""
            =g>
            isa goal
			phase traversal
            state process_target_check
            =imaginal>
            isa self
            reached True
            ==>
            =g>
            isa goal
			phase landmark
            state check_agent_nearby
            =imaginal>
            """,
        )

        # Direction decision logic
        actr_agent.productionstring(
            name="prepare direction decision",
            string="""
            =g>
            isa goal
			phase traversal
            state prepare_direction_decision
            ==>
            =g>
            isa goal
			phase traversal
            state choose_direction
            """,
        )
        for dir in ["up", "down", "left", "right"]:
            actr_agent.productionstring(
                name=f"choose direction {dir}",
                string=f"""
                =g>
                isa goal
                phase traversal
                state choose_direction
                ==>
                =g>
                isa goal
                phase traversal
                state find_path
                direction {dir}
                """,
            )

        # Blockade remembering
        actr_agent.productionstring(
            name="remember blockade",
            string="""
            =g>
            isa goal
			phase traversal
            state remember_blockade
            ==>
            =g>
            isa goal
			phase traversal
            state check_for_emergencies
            """,
        )

    def add_pathfinding_productions(self, actr_agent):
        """Adds productions used for pathfinding. These are used both in the traversal and in the landmark phase."""
        actr_agent.productionstring(
            name="find path",
            string="""
            =g>
            isa goal
            state find_path
            ==>
            =g>
            isa goal
            state fetch_path_step
            """,
        )
        actr_agent.productionstring(
            name="fetch path step",
            string="""
            =g>
            isa goal
            state fetch_path_step
            ?manual>
            state free
            ==>
            =g>
            isa goal
            state follow_path_step
            """,
        )
        actr_agent.productionstring(
            name="no path found",
            string="""
            =g>
            isa goal
            state follow_path_step
            path None
            ==>
            =g>
            isa goal
            state remember_blockade
            """,
        )
        for dir, key in [("left", "A"), ("right", "D"), ("up", "W"), ("down", "S")]:
            actr_agent.productionstring(
                name=f"move {dir}",
                string=f"""
                =g>
                isa goal
                state follow_path_step
                path {dir}
                ?manual>
                state free
                ==>
                =g>
                isa goal
                state fetch_path_step
                +manual>
                isa _manual
                cmd press_key
                key {key}
                """,
            )
        actr_agent.productionstring(
            name="path finished",
            string="""
            =g>
            isa goal
            state follow_path_step
            path finished
            ==>
            =g>
            isa goal
            state check_for_emergencies
            """,
        )

    def add_landmark_productions(self, actr_agent):
        """Add productions for the landmark phase, meaning when our agent has arrived at the target landmark. Includes checking for nearby agents, repairing and nominating."""
        # Nearby agent checking and handling
        actr_agent.productionstring(
            name="check agent nearby",
            string="""
            =g>
            isa goal
            phase landmark
            state check_agent_nearby
            ==>
            =g>
            isa goal
            phase landmark
            state decide_landmark_action
            """,
        )
        actr_agent.productionstring(
            name="no agent nearby",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_landmark_action
            =imaginal>
            isa self
            akey None
            ==>
            =g>
            isa goal
            phase landmark
            state check_repair_needed
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="agent nearby",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_landmark_action
            =imaginal>
            isa self
            akey ~None
            ==>
            =g>
            isa goal
            phase landmark
            state prepare_agent_action_decision
            =imaginal>
            """,
        )

        # Different actions towards spotted agent
        actr_agent.productionstring(
            name="prepare agent action decision",
            string="""
            =g>
            isa goal
            phase landmark
            state prepare_agent_action_decision
            ==>
            =g>
            isa goal
            phase landmark
            state decide_action_towards_agent
            """,
        )
        actr_agent.productionstring(
            name="begin agent observation",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_action_towards_agent
            =imaginal>
            isa self
            ==>
            =g>
            isa goal
            phase observation
            state observing
            monitor_agent_movement True
            =imaginal>
            isa self
            agent_movement None
            patience 3
            """,
        )
        actr_agent.productionstring(
            name="begin nomination",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_action_towards_agent
            ?manual>
            state free
            ==>
            =g>
            isa goal
            phase landmark
            state nominate
            +manual>
            isa _manual
            cmd press_key
            key N
            """,
        )
        actr_agent.productionstring(
            name="conclude nomination",
            string="""
            =g>
            isa goal
            phase landmark
            state nominate
            =imaginal>
            isa self
            akey =key
            ?manual>
            state free
            ==>
            =g>
            isa goal
            phase landmark
            state nominate
            +manual>
            isa _manual
            cmd press_key
            key =key
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="ignore agent",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_action_towards_agent
            ==>
            =g>
            isa goal
            phase landmark
            state check_repair_needed
            """,
        )
        actr_agent.productionstring(
            name="fully trust agent",
            string="""
            =g>
            isa goal
            phase landmark
            state decide_action_towards_agent
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            """,
        )

        # Repair checking and conducting
        actr_agent.productionstring(
            name="no repair needed",
            string="""
            =g>
            isa goal
            phase landmark
            state check_repair_needed
            =imaginal>
            isa self
            lstate intact
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="commence repair",
            string="""
            =g>
            isa goal
            phase landmark
            state check_repair_needed
            =imaginal>
            isa self
            lstate damaged
            ==>
            =g>
            isa goal
            phase landmark
            state find_path
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="arrived at landmark",
            string="""
            =g>
            isa goal
            phase landmark
            state check_for_emergencies
            ?manual>
            state free
            ==>
            =g>
            isa goal
            phase landmark
            state wait_for_repair
            +manual>
            isa _manual
            cmd press_key
            key R
            """,
        )
        actr_agent.productionstring(
            name="wait for repair",
            string="""
            =g>
            isa goal
            phase landmark
            state wait_for_repair
            =imaginal>
            isa self
            state_change ~repaired
            ==>
            =g>
            isa goal
            phase landmark
            state wait_for_repair
            =imaginal>
            """,
        )
        actr_agent.productionstring(
            name="repair complete",
            string="""
            =g>
            isa goal
            phase landmark
            state wait_for_repair
            =imaginal>
            isa self
            state_change repaired
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            =imaginal>
            isa self
            state_change None
            """,
        )

    def add_observation_productions(self, actr_agent):
        """Adds productions for the observation phase. Each production is for a different action the observed agent has taken."""
        # Different agent movement actions
        actr_agent.productionstring(
            name="observed movement towards damaged landmark",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate damaged
            agent_movement towards
            ==>
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            agent_movement None
            """,
        )
        actr_agent.productionstring(
            name="observed movement away from damaged landmark",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate damaged
            agent_movement away
            ==>
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            agent_movement None
            """,
        )
        actr_agent.productionstring(
            name="observed movement towards intact landmark",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate intact
            agent_movement towards
            ==>
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            agent_movement None
            """,
        )
        actr_agent.productionstring(
            name="observed movement away from intact landmark",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate intact
            agent_movement away
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            monitor_agent_movement False
            =imaginal>
            isa self
            agent_movement None
            """,
        )
        actr_agent.productionstring(
            name="observed still agent",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            agent_movement still
            ==>
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            agent_movement None
            """,
        )

        # Landmark manipulation actions
        actr_agent.productionstring(
            name="observed repair",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            state_change repair
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            monitor_agent_movement False
            =imaginal>
            isa self
            agent_movement None
            state_change None
            """,
        )
        actr_agent.productionstring(
            name="observed sabotage",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            state_change sabotaged
            ==>
            =g>
            isa goal
            phase landmark
            state find_path
            monitor_agent_movement False
            =imaginal>
            isa self
            agent_movement None
            state_change None
            """,
        )

        # Filler production while waiting for the agent to act
        actr_agent.productionstring(
            name="pending observation",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            ==>
            =g>
            isa goal
            phase observation
            state observing
            """,
            utility=-100,
        )

        # Observation ending because of no more patience
        actr_agent.productionstring(
            name="skip to repair",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate damaged
            patience 0
            ==>
            =g>
            isa goal
            phase landmark
            state find_path
            monitor_agent_movement False
            =imaginal>
            """,
            utility=100,
        )
        actr_agent.productionstring(
            name="skip to leave",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate intact
            patience 0
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            monitor_agent_movement False
            =imaginal>
            """,
            utility=100,
        )

        # Observation ending because agent left
        actr_agent.productionstring(
            name="skip to repair because agent left",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate damaged
            agent_movement gone
            ==>
            =g>
            isa goal
            phase landmark
            state find_path
            monitor_agent_movement False
            =imaginal>
            isa self
            agent_movement None
            """,
            utility=100,
        )
        actr_agent.productionstring(
            name="skip to leave because agent left",
            string="""
            =g>
            isa goal
            phase observation
            state observing
            =imaginal>
            isa self
            lstate intact
            agent_movement gone
            ==>
            =g>
            isa goal
            phase traversal
            state choose_landmark
            monitor_agent_movement False
            =imaginal>
            isa self
            agent_movement None
            """,
            utility=100,
        )
