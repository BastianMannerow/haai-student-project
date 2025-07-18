import heapq, random
from typing import Dict, List, Tuple, Optional, Union

import pyactr as actr
from simulation import LübeckACTR


get_goal,   set_goal    = LübeckACTR.get_goal,  LübeckACTR.set_goal
key_pressed             = LübeckACTR.key_pressed
check_damage            = LübeckACTR.check_location_damage



class GengarAdapter:

    WALKABLE = {"-","X","A","B","C","D","E","F"}
    OBSTACLE = {"Z"}
    SUS_WEIGHTS = {
        "Kam von beschädigter Landmarke": 1,
        "Weggegangen ohne zu reparieren": 2,
        "Neben frisch entdeckter beschädigter Landmarke": 1,
        "Was in Lights": 5,
    }
    NOMINATION_THRESHOLD = 5


    def __init__(self, agent_construct, agent_runner):
        self.agent_construct = agent_construct
        self.agent_runner    = agent_runner

        self.world_map:  List[List[str]] = [['~'] * 20 for _ in range(20)]
        self.current_plan: Optional[Dict[str, Union[int, str]]] = None
        self.key_queue:   List[str] = []
        self.last_agent_cells: List[Tuple[int, int]] = []

        #  soziale Erinnerung pro Agent
        self.social_memory: Dict[str, Dict[str, Union[
            int, Tuple[int, int], List[str]]]] = {}

        #  LM-Watch
        self.landmark_watch = dict(coords=None, was_damaged=None,
                                   prev_coords=None, prev_damaged=None)


    def extending_actr(self):
        self._update_world_state()

        # druecke key
        if self._dispatch_queued_key():
            return

        # Plan sicherstellen
        if self.current_plan is None:
            self._acquire_or_create_plan()
        if not self.current_plan:
            return

        pos = self._get_agent_pos()
        ay, ax = pos if pos else (-1, -1)
        gy, gx = self.current_plan['goaly'], self.current_plan['goalx']

        # Beschädigte Landmarke in LOS > alles
        dmg = self._first_damaged_landmark_in_los()
        if dmg:
            dy, dx = dmg
            # repariere
            if (ay, ax) == (dy, dx):
                print("Beschädigte Landmarke unter mir → Reparatur.")
                self._start_repair_plan(dx, dy);  return
            # sonst Kurs ändern
            print("Beschädigte Landmarke gesehen → Plan überschrieben.")
            self.key_queue.clear()
            self.current_plan = dict(goalname="repair_target",
                                     goalx=dx, goaly=dy,
                                     status="going_to_repair",
                                     suspicion_checked=False)
            gy, gx = dy, dx

        # Ziel sichtbar & intakt? dann überspringen bre
        if (0 <= gy < 20 and 0 <= gx < 20 and self.world_map[gy][gx] == 'X'
                and not check_damage(self.agent_construct)):
            print("Ziel-Landmarke ist intakt → überspringe.")
            self.current_plan = None;  return

        # Am Ziel?
        if pos and (ay, ax) == (gy, gx):
            if check_damage(self.agent_construct):
                if not self.current_plan.get("suspicion_checked"):
                    self._run_suspicion_checks()
                    self.current_plan["suspicion_checked"] = True
                print("Stehe auf beschädigter Landmarke → Reparatur.")
                self._start_repair_plan(ax, ay);  return
            else:
                print("Landmarke erreicht → neuen Plan wählen.")
                self.current_plan = None;  return

        # Navigation
        path = (self._astar_path(pos, (gy, gx)) or
                self._path_to_best_frontier(pos, (gy, gx)) or
                self._path_to_nearest_unknown(pos, (gy, gx)))
        if path:
            self.key_queue = path
            self._push_key_to_goal(self.key_queue.pop(0))
        else:
            print("Blockiert – kein Weg gefunden.")


    # Queue abschließen / Taste erneut schicken
    def _dispatch_queued_key(self) -> bool:
        if not self.key_queue:
            return False
        key = self.key_queue[0]

        # Sonderfall: Nomination-Tasten nicht durch _push_key_to_goal
        if key not in "WASD":
            self._send_manual_key(key)
            self.key_queue.pop(0)
            return True

        if key_pressed(self.agent_construct) == key:
            self.key_queue.pop(0)
        elif key_pressed(self.agent_construct) is None:
            self._push_key_to_goal(key)
        return True

    def _send_manual_key(self, k: str):
        """Schreibt ein press_key-Chunk"""
        chunk = actr.makechunk(typename="press_key", key=k)
        set_goal(self.agent_construct.actr_agent, chunk)
        print(f"Sende Tastendruck {k}")

    # Plan wiederverwenden oder neu wählen
    def _acquire_or_create_plan(self):
        ag = self.agent_construct.actr_agent

        # Goal-Buffer wiederverwenden
        gbuf = get_goal(ag)
        if gbuf:
            ch = next(iter(gbuf))
            if ch.typename == "moveplan":
                self.current_plan = {k: int(str(v)) if k in ('goalx','goaly') else v
                                     for k, v in dict(ch).items() if k != 'direction'}
                set_goal(ag, actr.makechunk(**self.current_plan))
                return

        # waehle random LM
        lm_chunks = [c for c in ag.decmem if c.typename == "landmark"]
        if not lm_chunks:
            return
        lm = random.choice(lm_chunks)
        self.current_plan = dict(goalname=lm.name,
                                 goalx=int(str(lm.x)),
                                 goaly=int(str(lm.y)),
                                 status="planning")
        print("Neuer Plan:", self.current_plan)

    # Karten- & Social-Update
    def _update_world_state(self):
        LOS = 3

        # alte Agent-Marker löschen
        for y, x in self.last_agent_cells:
            if self.world_map[y][x] in ("A", "B"):
                self.world_map[y][x] = '-'
        self.last_agent_cells.clear()

        # aktuelle Stimuli eintragen
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                y, x = st['position'];  ch = st['text']
                if 0 <= y < 20 and 0 <= x < 20:
                    self.world_map[y][x] = ch
                if ch in ("A","B"):
                    self.last_agent_cells.append((y, x))

        # unbekannte Felder aufdecken
        pos = self._get_agent_pos()
        if pos:
            ay, ax = pos
            for dy in range(-LOS, LOS+1):
                for dx in range(-LOS, LOS+1):
                    ny, nx = ay+dy, ax+dx
                    if 0 <= ny < 20 and 0 <= nx < 20 and self.world_map[ny][nx] == '~':
                        self.world_map[ny][nx] = '-'

        self._update_social_memory()
        self._refresh_landmark_watch()
        self._check_damage_flip_suspicion()

    # Social memory
    def _update_social_memory(self):
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                sym = st['text']
                if sym in self.agent_runner.other_agents_key_list:
                    y, x = st['position']
                    entry = self.social_memory.setdefault(sym,
                              dict(name=sym, suspicion=0, reasons=[],
                                   last_seen=(y,x)))
                    entry.update(last_seen=(y,x))

    def _increase_sus(self, sym: str, reason: str):
        """Erhöht den SUS wert."""
        pts = self.SUS_WEIGHTS.get(reason, 1)  # default = 1
        entry = self.social_memory.setdefault(
            sym,
            dict(name=sym, suspicion=0, reasons=[], last_seen=None)
        )
        entry["suspicion"] += pts
        entry["reasons"].append(f"{reason} (+{pts})")
        print(f"\033[1;30;103m[SOCIAL] {sym}: Sus {entry['suspicion']}  Reason: {reason} (+{pts})\033[0m")

        # Nominierungs-Trigger
        if (entry['suspicion'] >= self.NOMINATION_THRESHOLD
                and sym not in getattr(self, "_already_nominated", set())):
            # N + Buchstabe in die Warteschlange
            self.key_queue = ['N', sym] + self.key_queue
            print(f"\033[1;97;45m[IMPOSTER-VOTE] nominiere {sym}\033[0m")

    # Verdachtsregeln
    def _run_suspicion_checks(self):
        for sym in self.social_memory:
            if self._rule_came_from_damaged(sym):
                continue
            if self._rule_left_without_repair(sym):
                continue

    # kam aus Richtung Ziel-Landmarke und beschädigt
    def _rule_came_from_damaged(self, sym):
        if not self.current_plan or not check_damage(self.agent_construct):
            return False
        gy, gx = self.current_plan['goaly'], self.current_plan['goalx']
        ly, lx = self.social_memory[sym]['last_seen']
        if abs(ly-gy)+abs(lx-gx) <= 3:
            self._increase_sus(sym, "Kam von beschädigter Landmarke")
            return True
        return False

    # stand daneben, ist jetzt weg
    def _rule_left_without_repair(self, sym):
        if not self.current_plan or not check_damage(self.agent_construct):
            return False
        gy, gx = self.current_plan['goaly'], self.current_plan['goalx']
        ly, lx = self.social_memory[sym]['last_seen']
        if abs(ly-gy)+abs(lx-gx) > 5:
            return False
        # noch sichtbar?
        if any(st['text']==sym for sd in self.agent_construct.stimuli for st in sd.values()):
            return False
        self._increase_sus(sym, "Weggegangen ohne zu reparieren")
        return True

    # Landmarke wird in LOS plötzlich beschädigt
    def _check_damage_flip_suspicion(self):
        w = self.landmark_watch
        if w['prev_coords'] is None or w['prev_damaged'] or not w['was_damaged']:
            return
        gy, gx = w['coords']
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                sym = st['text']
                if sym in self.agent_runner.other_agents_key_list:
                    ay, ax = st['position']
                    if abs(ay-gy)+abs(ax-gx) <= 1:
                        self._increase_sus(sym, "Was in Lights")



    # LM-Watch-Update
    def _refresh_landmark_watch(self):
        prev_c, prev_d = self.landmark_watch['coords'], self.landmark_watch['was_damaged']
        coord = None
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                if st['text'] == 'X':
                    coord = st['position'];  break
            if coord: break
        damaged = check_damage(self.agent_construct) if coord else None
        self.landmark_watch.update(coords=coord, was_damaged=damaged,
                                   prev_coords=prev_c, prev_damaged=prev_d)

    # Damaged Landmark in LOS
    def _first_damaged_landmark_in_los(self) -> Optional[Tuple[int,int]]:
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                if st['text'] == 'X':
                    if check_damage(self.agent_construct):
                        return st['position']
        return None

    # Reparatur-Plan
    def _start_repair_plan(self, x, y):
        chunk = actr.makechunk(
            typename="repairplan",
            plan="repair", goalx=x, goaly=y,
            direction="R", status="pending"
        )
        set_goal(self.agent_construct.actr_agent, chunk)

    # Bewegung tut gut
    def _get_agent_pos(self) -> Optional[Tuple[int,int]]:
        sym = self.agent_runner.this_agent_key
        for sd in self.agent_construct.stimuli:
            for st in sd.values():
                if st['text'] == sym:
                    return st['position']
        return None

    def _push_key_to_goal(self, key):
        pos = self._get_agent_pos()
        if not pos:  return
        dy, dx = dict(W=-1,S=1,A=0,D=0)[key], dict(W=0,S=0,A=-1,D=1)[key]
        ny, nx = pos[0]+dy, pos[1]+dx
        if not (0<=ny<20 and 0<=nx<20) or self.world_map[ny][nx] not in self.WALKABLE:
            print("Zug blockiert.")
            self.key_queue.clear();  self.current_plan=None;  return
        set_goal(self.agent_construct.actr_agent,
                 actr.makechunk(typename="moveplan",
                                **(self.current_plan | dict(direction=key))))
        print(f"Press {key}")

    # A* & Exploration
    def _astar_path(self, start, goal):
        if any(self.world_map[y][x]=='~' for y,x in (start,goal)):
            return None
        frontier=[(0,start)]; came={start:(None,None)}; cost={start:0}
        while frontier:
            _,cur=heapq.heappop(frontier)
            if cur==goal: break
            cy,cx=cur
            for k,dy,dx in [('W',-1,0),('S',1,0),('A',0,-1),('D',0,1)]:
                ny,nx=cy+dy,cx+dx
                if 0<=ny<20 and 0<=nx<20 and self.world_map[ny][nx] in self.WALKABLE:
                    new=cost[cur]+1
                    if (ny,nx) not in cost or new<cost[(ny,nx)]:
                        cost[(ny,nx)]=new
                        heapq.heappush(frontier,(new+abs(goal[0]-ny)+abs(goal[1]-nx),(ny,nx)))
                        came[(ny,nx)]=(cur,k)
        if goal not in came: return None
        path,n=[],goal
        while came[n][0]:
            n,k=came[n]; path.append(k)
        return path[::-1]

    # Waehle naechste pos die begehbar ist, welches nah am goal ist und erreichbar durch andere begehbare pos
    def _path_to_best_frontier(self,start,goal):
        best=None
        for y in range(20):
            for x in range(20):
                if self.world_map[y][x]!='-': continue
                if not any(self.world_map[ny][nx]=='~'
                           for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]
                           if 0<=ny<20 and 0<=nx<20): continue
                p1=self._astar_path(start,(y,x))
                p2=self._astar_path((y,x),goal)
                if p1 and p2:
                    tot=len(p1)+len(p2)
                    if best is None or tot<best[0]:
                        best=(tot,p1)
        return best[1] if best else None

    # nehme naechste pos die unbekannt ist
    def _path_to_nearest_unknown(self,start,hint):
        best=None
        for y in range(20):
            for x in range(20):
                if self.world_map[y][x]!='~': continue
                for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                    if 0<=ny<20 and 0<=nx<20 and self.world_map[ny][nx] in self.WALKABLE:
                        p=self._astar_path(start,(ny,nx))
                        if p:
                            d=abs(hint[0]-y)+abs(hint[1]-x)
                            if best is None or d<best[0]:
                                best=(d,p); break
        return best[1] if best else None
