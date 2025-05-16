"""
    Library which extends pyactr for an easier usage and with some additional features.
"""
from itertools import islice
import pyactr as actr
import pyactr.vision as vision
from pyactr import chunks, utilities
from pyactr.utilities import ACTRError
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

def production_fired(agent, production_name): #TODO
    event = agent_construct.simulation.current_event
    print(event)
    return True


def set_goal(agent, chunk):
    first_goal = next(iter(agent.goals.values()))
    first_goal.add(chunk)

def get_imaginal(agent, index):
    goals = agent.goals
    try:
        key = next(islice(goals.keys(), index, index + 1))
        value = next(islice(goals.values(), index, index + 1))
    except StopIteration:
        raise IndexError("index out of range")

    print(f"key  #{index}: {key}")
    print(f"value#{index}: {value}")


def set_imaginal(agent, new_chunk, index):
    """
    Fügt `new_chunk` zum Goal an Position `index` in agent.goals hinzu.
    Das Goal-Objekt muss eine .add()-Methode haben (z.B. ein Set).
    """
    goals = agent.goals
    try:
        # Schlüssel und Wert an der gewünschten Position ermitteln
        key = next(islice(goals.keys(), index, index + 1))
        value = next(islice(goals.values(), index, index + 1))
    except StopIteration:
        raise IndexError(f"Index {index} out of range for goals (size={len(goals)})")

    # neues Chunk hinzufügen
    value.add(new_chunk)

    # Ausgabe zur Kontrolle
    print(f"key  #{index}: {key}")
    print(f"value#{index}: {value}")

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