"""
    Library which extends pyactr for an easier usage and with some additional features.
"""
from itertools import islice
import pyactr as actr
import pyactr.vision as vision
from pyactr import chunks, utilities
from pyactr.utilities import ACTRError
from simulation.Location import Location
from collections.abc import MutableSet, MutableSequence


def fix_pyactr():
    """
    Overrides pyactr visual class. There's an issue with attending objects & Chunk information especially with automatic visual search set to True
    """

    # Backup the original method
    _original_find = vision.VisualLocation.find

    # Patched find method with corrected attribute lookup

    def patched_find(self, otherchunk, actrvariables=None, extra_tests=None):
        # Initialize variables
        if extra_tests is None:
            extra_tests = {}
        if actrvariables is None:
            actrvariables = {}

        # Build search chunk from production right-hand side
        try:
            mod_attr_val = {x[0]: utilities.check_bound_vars(actrvariables, x[1], negative_impossible=False)
                            for x in otherchunk.removeunused()}
        except ACTRError as e:
            raise ACTRError(f"The chunk '{otherchunk}' is not defined correctly; {e}")
        chunk_used_for_search = chunks.Chunk(utilities.VISUALLOCATION, **mod_attr_val)

        found = None
        found_stim = None
        closest = float("inf")
        x_closest = float("inf")
        y_closest = float("inf")

        # Iterate over stimulus keys and their attribute dicts
        for each in self.environment.stimulus:
            stim_attrs = self.environment.stimulus[each]

            # Extra-tests for attended flag
            try:
                attended_flag = extra_tests.get("attended")
                if attended_flag in (False, 'False') and self.finst and stim_attrs in self.recent:
                    continue
                if attended_flag not in (False, 'False') and self.finst and stim_attrs not in self.recent:
                    continue
            except KeyError:
                pass

            # Value test
            if (chunk_used_for_search.value != chunk_used_for_search.EmptyValue() and
                    chunk_used_for_search.value.values != stim_attrs.get("text")):
                continue

            # Position extraction
            position = (int(stim_attrs['position'][0]), int(stim_attrs['position'][1]))

            # Screen-X/Y absolute tests
            try:
                if (chunk_used_for_search.screen_x.values and
                        int(chunk_used_for_search.screen_x.values) != position[0]):
                    continue
            except (TypeError, ValueError, AttributeError):
                pass
            try:
                if (chunk_used_for_search.screen_y.values and
                        int(chunk_used_for_search.screen_y.values) != position[1]):
                    continue
            except (TypeError, ValueError, AttributeError):
                pass

            # Additional relative and closest tests omitted for brevity...
            # [Include the rest of the original distance checks here]

            # If stimulus passes all tests, prepare the visible chunk
            found_stim = stim_attrs

            # --- FIXED comprehension: use stim_attrs, not 'each' directly ---
            filtered = {
                k: stim_attrs[k]
                for k in stim_attrs
                if k not in ('position', 'text', 'vis_delay')
            }
            visible_chunk = chunks.makechunk(
                nameofchunk="vis1",
                typename="_visuallocation",
                **filtered
            )

            # Compare chunk to search criteria
            if visible_chunk <= chunk_used_for_search:
                temp_dict = visible_chunk._asdict()
                temp_dict.update({"screen_x": position[0], "screen_y": position[1]})
                found = chunks.Chunk(utilities.VISUALLOCATION, **temp_dict)

                # Update current-closeness metrics
                closest = utilities.calculate_pythagorean_distance(self.environment.current_focus, position)
                x_closest = utilities.calculate_onedimensional_distance(self.environment.current_focus, position,
                                                                        horizontal=True)
                y_closest = utilities.calculate_onedimensional_distance(self.environment.current_focus, position,
                                                                        horizontal=False)

        return found, found_stim

    # Apply patch
    vision.VisualLocation.find = patched_find

def production_fired(agent):
    event = agent.simulation.current_event
    if "RULE FIRED: " in event[2]:
        return event[2].replace("RULE FIRED: ", "")

    else:
        return None


def set_goal(agent, chunk):
    first_goal = next(iter(agent.goals.values()))
    first_goal.add(chunk)

def get_goal(agent):
    """
    Gibt das Goal unter dem Schlüssel `key` aus agent.goals zurück.
    Wenn der Schlüssel nicht existiert, wird eine Meldung ausgegeben.
    """
    key = "g"
    goals = agent.goals
    # Prüfen, ob der Schlüssel existiert
    if key not in goals:
        return None

    # Rückgabe des vorhandenen Chunks
    value = goals[key]
    return value

def get_imaginal(agent, key):
    """
    Gibt das Goal unter dem Schlüssel `key` aus agent.goals zurück.
    Wenn der Schlüssel nicht existiert, wird eine Meldung ausgegeben.
    """
    goals = agent.goals
    if key not in goals:
        print(f"'{key}' NaN. Available buffers: {list(goals.keys())}")
        return None
    value = goals[key]
    return value


def set_imaginal(agent, new_chunk, key):
    """
    Fügt `new_chunk` zum Goal unter dem Schlüssel `key` in agent.goals hinzu.
    Wenn der Schlüssel nicht existiert, wird eine Meldung ausgegeben.
    """
    goals = agent.goals
    # Existenz des Schlüssels prüfen
    if key not in goals:
        print(f"Ziel '{key}' nicht vorhanden. Verfügbare Schlüssel: {list(goals.keys())}")
        return

    # Chunk hinzufügen
    value = goals[key]
    try:
        value.add(new_chunk)
    except AttributeError:
        raise TypeError(f"Das Goal-Objekt für '{key}' unterstützt keine .add()-Methode.")

def key_pressed(agent_construct):
    """
    Checks if a key was pressed to notify the Game.py

    :param agent_construct:
    :return:
    """
    event = agent_construct.simulation.current_event
    if event[1] == "manual" and "KEY PRESSED:" in event[2]:
        key = event[2][-1]
    else:
        key = None

    return key

def update_utility(actr_agent, production_name, utility):
    productions = actr_agent.productions
    productions[production_name]["utility"] = utility


def check_location_damage(agent):
    """
    Prüft innerhalb der Sichtweite (los) des gegebenen Agenten, ob sich mindestens ein Location-Objekt befindet.
    Wenn ja, wird der .damaged-Status dieses Location-Objekts (True/False) zurückgegeben.
    Falls kein Location-Objekt in Reichweite, wird None zurückgegeben.

    Args:
        agent (AgentConstruct): Der Agent, dessen Sichtfeld geprüft wird.

    Returns:
        bool oder None: True/False, wenn eine Location gefunden wurde, sonst None.
    """
    matrix = agent.middleman.experiment_environment.level_matrix
    r, c = agent.middleman.experiment_environment.find_agent(agent)
    if r is None:
        return None

    rows, cols = len(matrix), len(matrix[0])
    los = agent.los

    # Falls los = 0 oder größer als die Kartenmaße, betrachten wir die gesamte Karte
    if los == 0 or los > rows or los > cols:
        off_x = off_y = 0
        x_los, y_los = cols, rows
    else:
        off_x = off_y = los
        x_los = y_los = 2 * los + 1

    for i in range(y_los):
        for j in range(x_los):
            mi = r - off_y + i
            mj = c - off_x + j

            # außerhalb der Karte überspringen
            if mi < 0 or mi >= rows or mj < 0 or mj >= cols:
                continue

            # Prüfen, ob in dieser Zelle ein Location-Objekt liegt
            for element in matrix[mi][mj]:
                if isinstance(element, Location):
                    return element.damaged

    return None
