from agents.Mew import Mew
from agents.MewAdapter import MewAdapter

# Only to avoid overloading the simulation. Returns the Agent object needed.
class AgentTypeReturner:
    def __init__(self):
        pass

    # Create an agent object based on the type
    def return_agent_type(self, name, actr_environment, agent_id_list):
        if name == "Human":
            return None

        elif name == "Mew":
            runner = Mew(actr_environment)
            return runner, runner.build_agent(agent_id_list), MewAdapter(actr_environment)

        else:
            raise ValueError(f"Unknown Agent .py Type: {name}")