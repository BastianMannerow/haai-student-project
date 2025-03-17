from agents.Basti import Basti
from agents.BastiAdapter import BastiAdapter
from agents.Runner import Runner
from agents.RunnerAdapter import RunnerAdapter
from agents.Hunter import Hunter
from agents.HunterAdapter import HunterAdapter

# Only to avoid overloading the simulation. Returns the Agent object needed.
class AgentTypeReturner:
    def __init__(self):
        pass

    # Create an agent object based on the type
    def return_agent_type(self, name, actr_environment, agent_id_list):
        if name == "Human":
            return None

        elif name == "Basti":
            basti = Basti(actr_environment)
            return basti, basti.build_agent(agent_id_list), BastiAdapter(actr_environment)

        elif name == "Runner":
            runner = Runner(actr_environment)
            return runner, runner.build_agent(agent_id_list), RunnerAdapter(actr_environment)

        elif name == "Hunter":
            hunter = Hunter(actr_environment)
            return hunter, hunter.build_agent(agent_id_list), HunterAdapter(actr_environment)

        else:
            raise ValueError(f"Unknown Agent .py Type: {name}")