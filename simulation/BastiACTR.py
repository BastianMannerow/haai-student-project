"""
    Library which extends pyactr for an easier usage and with some additional features.
"""
from itertools import islice
import pyactr as actr


def compare_goal(agent, compare_goal):
    """
    Compares the goal of the agent with the given goal.

    Args:
        agent (pyactr agent): Parent of the SocialAgent
        goal (str): The goal

    Returns:
        boolean
    """
    goals = agent.goals
    goal = str(next(iter(goals.values())))

    print(goal)

    return "Hallo"


def compare_imaginal(agent, compare_imaginal):
    """
    Compares the goal of the agent with the given goal.

    Args:
        agent (pyactr agent): Parent of the SocialAgent
        goal (str): The goal

    Returns:
        boolean
    """

    goals = agent.goals
    imaginal = str(next(islice(goals.values(), 1, 2)))

    return "Hallo"


def rule_fired(agent, rule_name):
    event = agent_construct.simulation.current_event
    return True


def set_goal(agent, goal):
    first_goal = next(iter(agent.goals.values()))
    first_goal.add(actr.chunkstring(
        string=f"isa {self.goal_phases[0]} state {self.goal_phases[0]}RememberedPunishment"))


def key_pressed(agent_construct):
    event = agent_construct.simulation.current_event
    if event[1] == "manual" and "KEY PRESSED:" in event[2]:
        key = event[2][-1]
    else:
        key = None

    return key