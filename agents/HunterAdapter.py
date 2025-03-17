from simulation import BastiACTR

class HunterAdapter:
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

    # Extending ACT-R
    def extending_actr(self, agent_construct):
        """
        Functionality, which extends ACT-R
        In pyactr, ACT-R functionality and regular arithmetic or logical functions are strictly divided.
        The reason for that is a clearer understanding of the agents' behaviour.
        This method will supervise the internal state of the agent.

        Args:
            agent_construct (AgentConstruct): Parent of the SocialAgent
        """

        if BastiACTR.compare_goal(agent_construct, "testStart"):
            print(agent_construct.actr_agent.decmem)

        if BastiACTR.compare_imaginal(agent_construct, "test"):
            BastiACTR.set_goal(agent_construct, "test")

        if BastiACTR.rule_fired(agent_construct, "test"):
            pass