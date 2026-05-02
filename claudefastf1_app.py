"""
╔══════════════════════════════════════════════════════════════╗
║         F1 ULTRA-REALISTIC RACE SIMULATION ENGINE           ║
║   Monte Carlo | Tire Physics | Weather | Strategy | DRS     ║
╚══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, jsonify, request, make_response
import threading, time, random, math, json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import statistics

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response

# ─────────────────────────────────────────────────────────────────────────────
#  DATA LAYER — 2024 SEASON REALISTIC DRIVER & TEAM PROFILES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DriverProfile:
    name: str
    team: str
    number: int
    skill: float
    consistency: float
    wet_skill: float
    overtaking: float
    tire_mgmt: float
    qualifying_pace: float
    mental: float
    color: str
    elo: float = 1500.0

@dataclass
class TeamProfile:
    name: str
    car_pace: float
    reliability: float
    aero_efficiency: float
    pit_crew_speed: float
    strategy_iq: float
    color: str

@dataclass
class TireCompound:
    name: str
    base_pace: float
    deg_rate: float
    cliff_lap: int
    cliff_severity: float
    warmup_laps: int
    color: str

@dataclass
class RaceState:
    lap: int = 0
    total_laps: int = 57
    weather: str = "dry"
    safety_car_active: bool = False
    vsc_active: bool = False
    results: List = field(default_factory=list)
    lap_times: Dict = field(default_factory=dict)
    positions: Dict = field(default_factory=dict)
    gaps: Dict = field(default_factory=dict)
    dnf_list: List = field(default_factory=list)
    pit_windows: Dict = field(default_factory=dict)
    strategy_log: List = field(default_factory=list)
    running: bool = False
    finished: bool = False


DRIVERS: Dict[str, DriverProfile] = {
    "VER": DriverProfile("Max Verstappen",    "Red Bull Racing",  1,  99, 97, 95, 96, 94, 99, 98, "#3671C6"),
    "NOR": DriverProfile("Lando Norris",      "McLaren",         4,  95, 92, 88, 93, 90, 94, 91, "#FF8000"),
    "LEC": DriverProfile("Charles Leclerc",   "Ferrari",         16, 94, 90, 86, 91, 87, 97, 88, "#E8002D"),
    "PIA": DriverProfile("Oscar Piastri",     "McLaren",         81, 90, 88, 84, 88, 87, 91, 87, "#FF8000"),
    "SAI": DriverProfile("Carlos Sainz",      "Ferrari",         55, 91, 93, 89, 89, 92, 90, 91, "#E8002D"),
    "HAM": DriverProfile("Lewis Hamilton",    "Mercedes",        44, 93, 94, 96, 95, 95, 92, 96, "#27F4D2"),
    "RUS": DriverProfile("George Russell",    "Mercedes",        63, 89, 91, 87, 88, 89, 91, 89, "#27F4D2"),
    "PER": DriverProfile("Sergio Perez",      "Red Bull Racing", 11, 88, 86, 82, 85, 91, 87, 83, "#3671C6"),
    "ALO": DriverProfile("Fernando Alonso",   "Aston Martin",    14, 90, 95, 94, 92, 96, 89, 97, "#358C75"),
    "STR": DriverProfile("Lance Stroll",      "Aston Martin",    18, 79, 78, 76, 76, 79, 79, 74, "#358C75"),
    "GAS": DriverProfile("Pierre Gasly",      "Alpine",          10, 82, 84, 80, 83, 81, 82, 82, "#0093CC"),
    "OCO": DriverProfile("Esteban Ocon",      "Alpine",          31, 80, 83, 79, 81, 82, 80, 80, "#0093CC"),
    "ALB": DriverProfile("Alexander Albon",   "Williams",        23, 81, 85, 82, 82, 83, 80, 83, "#64C4FF"),
    "SAR": DriverProfile("Logan Sargeant",    "Williams",        2,  72, 71, 69, 71, 70, 73, 68, "#64C4FF"),
    "TSU": DriverProfile("Yuki Tsunoda",      "RB",              22, 82, 80, 78, 84, 79, 83, 79, "#6692FF"),
    "LAW": DriverProfile("Liam Lawson",       "RB",              40, 80, 79, 77, 82, 78, 81, 78, "#6692FF"),
    "HUL": DriverProfile("Nico Hülkenberg",   "Haas",            27, 81, 84, 82, 80, 84, 80, 83, "#B6BABD"),
    "MAG": DriverProfile("Kevin Magnussen",   "Haas",            20, 79, 75, 77, 82, 76, 79, 77, "#B6BABD"),
    "BOT": DriverProfile("Valtteri Bottas",   "Sauber",          77, 83, 85, 80, 81, 86, 84, 82, "#52E252"),
    "ZHO": DriverProfile("Guanyu Zhou",       "Sauber",          24, 76, 78, 73, 74, 79, 75, 75, "#52E252"),
}

TEAMS: Dict[str, TeamProfile] = {
    "Red Bull Racing": TeamProfile("Red Bull Racing", 98, 95, 97, 2.3, 95, "#3671C6"),
    "McLaren":         TeamProfile("McLaren",          96, 93, 95, 2.5, 90, "#FF8000"),
    "Ferrari":         TeamProfile("Ferrari",          94, 91, 93, 2.6, 82, "#E8002D"),
    "Mercedes":        TeamProfile("Mercedes",         92, 94, 92, 2.4, 88, "#27F4D2"),
    "Aston Martin":    TeamProfile("Aston Martin",     85, 92, 84, 2.7, 80, "#358C75"),
    "Alpine":          TeamProfile("Alpine",           81, 89, 80, 2.8, 75, "#0093CC"),
    "Williams":        TeamProfile("Williams",         79, 90, 78, 2.9, 73, "#64C4FF"),
    "RB":              TeamProfile("RB",               80, 91, 79, 2.8, 74, "#6692FF"),
    "Haas":            TeamProfile("Haas",             78, 88, 77, 3.0, 70, "#B6BABD"),
    "Sauber":          TeamProfile("Sauber",           76, 87, 75, 3.1, 68, "#52E252"),
}

TIRE_COMPOUNDS: Dict[str, TireCompound] = {
    "soft":   TireCompound("Soft",   0.0,   0.085, 18, 0.15, 1, "#FF1E1E"),
    "medium": TireCompound("Medium", 0.55,  0.045, 28, 0.10, 2, "#FFD700"),
    "hard":   TireCompound("Hard",   1.10,  0.025, 40, 0.08, 3, "#E8E8E8"),
    "inter":  TireCompound("Inter",  0.80,  0.060, 22, 0.12, 2, "#39B54A"),
    "wet":    TireCompound("Wet",    2.50,  0.030, 35, 0.07, 3, "#0067FF"),
}

BASE_LAP_TIME = 90.0


# ─────────────────────────────────────────────────────────────────────────────
#  PHYSICS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def compute_lap_time(driver_id: str, tire: TireCompound, tire_age: int,
                     fuel_load: float, weather: str, sc_active: bool,
                     vsc_active: bool, drs_available: bool) -> Tuple[float, float]:
    driver = DRIVERS[driver_id]
    team   = TEAMS[driver.team]

    car_delta    = (100 - team.car_pace) * 0.04
    driver_delta = (100 - driver.skill) * 0.025

    base_tire_time = tire.base_pace
    if tire_age <= tire.warmup_laps:
        base_tire_time += (tire.warmup_laps - tire_age + 1) * 0.12

    linear_deg = tire_age * tire.deg_rate
    cliff_deg  = 0.0
    if tire_age > tire.cliff_lap:
        cliff_age = tire_age - tire.cliff_lap
        cliff_deg = cliff_age * tire.cliff_severity * (1.0 - (driver.tire_mgmt / 100) * 0.4)

    tire_total  = base_tire_time + linear_deg + cliff_deg
    fuel_delta  = fuel_load * 3.85

    weather_delta = 0.0
    if weather == "wet":
        weather_delta = 8.0 * (1.0 - (driver.wet_skill / 100) * 0.6) + random.gauss(0, 0.5)
    elif weather == "damp":
        weather_delta = 3.5 * (1.0 - (driver.wet_skill / 100) * 0.4) + random.gauss(0, 0.3)

    drs_delta   = -0.30 if drs_available else 0.0
    sc_delta    = 25.0 if sc_active else (8.0 if vsc_active else 0.0)
    noise_sigma = (100 - driver.consistency) * 0.008 + 0.05
    noise       = random.gauss(0, noise_sigma)

    raw_pace = BASE_LAP_TIME + car_delta + driver_delta
    lap_time = raw_pace + tire_total + fuel_delta + weather_delta + drs_delta + sc_delta + noise
    return round(lap_time, 3), round(raw_pace, 3)


def should_pit(driver_id: str, tire: TireCompound, tire_age: int,
               laps_remaining: int, strategy_iq: float) -> bool:
    if tire_age > tire.cliff_lap + 5:
        return True
    if tire.name == "Soft" and tire_age > tire.cliff_lap - 2 and laps_remaining > 12:
        return True
    proactive_lap = tire.cliff_lap - int(strategy_iq / 20)
    if tire_age >= proactive_lap and laps_remaining > 10:
        return random.random() < 0.35
    return False


def compute_pit_time(team: TeamProfile) -> float:
    stationary = 2.2 + random.gauss(0, 0.15) + team.pit_crew_speed * 0.1
    inout_loss  = 18.5 + random.gauss(0, 0.8)
    return round(stationary + inout_loss, 2)


def overtake_probability(attacker: str, defender: str, gap: float, weather: str) -> float:
    att = DRIVERS[attacker]
    dff = DRIVERS[defender]
    if gap > 1.2 or gap < 0.0:
        return 0.0
    base     = (att.overtaking - dff.overtaking) * 0.008 + 0.12
    drs_boost = 0.18 if gap < 0.8 else 0.0
    wet_mod   = 0.06 if weather == "wet" else 0.0
    return max(0.02, min(0.75, base + drs_boost + wet_mod))


# ─────────────────────────────────────────────────────────────────────────────
#  MONTE CARLO ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def monte_carlo_race(n_sims: int = 1000, track_laps: int = 57,
                     weather_mode: str = "dry",
                     selected_drivers: Optional[List[str]] = None) -> Dict:
    active = selected_drivers or list(DRIVERS.keys())[:20]
    win_counts       = defaultdict(int)
    podium_counts    = defaultdict(int)
    points_total     = defaultdict(float)
    finish_positions = defaultdict(list)
    dnf_counts       = defaultdict(int)
    avg_lap_times    = defaultdict(list)

    POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

    for sim in range(n_sims):
        race_weather = weather_mode
        if weather_mode == "random":
            r = random.random()
            race_weather = "wet" if r < 0.18 else ("damp" if r < 0.35 else "dry")

        grid = []
        for drv in active:
            q_t = (100 - DRIVERS[drv].qualifying_pace) * 0.03 + random.gauss(0, 0.12)
            grid.append((drv, q_t))
        grid.sort(key=lambda x: x[1])
        grid_order = [g[0] for g in grid]

        cumulative = {drv: i * 0.5 for i, drv in enumerate(grid_order)}
        tires      = {drv: ("soft" if i < 10 else "medium") for i, drv in enumerate(grid_order)}
        tire_age   = {drv: 0 for drv in grid_order}
        has_pitted = defaultdict(int)
        dnf_set    = set()

        for lap in range(1, track_laps + 1):
            fuel_frac = 1.0 - (lap / track_laps)
            sc_lap    = random.random() < 0.04 and lap > 3
            vsc_lap   = (not sc_lap) and random.random() < 0.03

            for drv in list(grid_order):
                if drv in dnf_set:
                    continue
                team_obj = TEAMS[DRIVERS[drv].team]
                if random.random() < (1 - team_obj.reliability / 100) * 0.002:
                    dnf_set.add(drv)
                    continue

                compound  = TIRE_COMPOUNDS[tires[drv]]
                tire_age[drv] += 1
                laps_left = track_laps - lap

                if laps_left > 3 and should_pit(drv, compound, tire_age[drv],
                                                  laps_left, team_obj.strategy_iq):
                    cumulative[drv] += compute_pit_time(team_obj)
                    has_pitted[drv] += 1
                    tires[drv] = ("medium" if laps_left > 25 else
                                  ("hard" if laps_left > 12 else "soft"))
                    if race_weather in ("wet", "damp"):
                        tires[drv] = "inter"
                    tire_age[drv] = 0

                if race_weather == "wet" and tires[drv] in ("soft", "medium", "hard"):
                    cumulative[drv] += compute_pit_time(team_obj)
                    tires[drv] = "wet"
                    tire_age[drv] = 0

                compound = TIRE_COMPOUNDS[tires[drv]]
                lap_t, _ = compute_lap_time(drv, compound, tire_age[drv], fuel_frac,
                                             race_weather, sc_lap, vsc_lap, random.random() < 0.45)
                cumulative[drv] += lap_t
                avg_lap_times[drv].append(lap_t)

        finishers = sorted([(d, t) for d, t in cumulative.items() if d not in dnf_set],
                            key=lambda x: x[1])
        final_order = [d for d, _ in finishers] + list(dnf_set)

        for pos, drv in enumerate(final_order):
            finish_positions[drv].append(pos + 1)
            if drv in dnf_set:
                dnf_counts[drv] += 1
                continue
            if pos == 0: win_counts[drv] += 1
            if pos < 3:  podium_counts[drv] += 1
            if pos < 10: points_total[drv] += POINTS[pos]

    results = []
    for drv in active:
        avg_finish = statistics.mean(finish_positions[drv]) if finish_positions[drv] else 20
        avg_lt     = statistics.mean(avg_lap_times[drv]) if avg_lap_times[drv] else 90.0
        results.append({
            "driver_id":    drv,
            "name":         DRIVERS[drv].name,
            "team":         DRIVERS[drv].team,
            "color":        DRIVERS[drv].color,
            "number":       DRIVERS[drv].number,
            "win_pct":      round(win_counts[drv] / n_sims * 100, 2),
            "podium_pct":   round(podium_counts[drv] / n_sims * 100, 2),
            "avg_points":   round(points_total[drv] / n_sims, 2),
            "avg_finish":   round(avg_finish, 2),
            "dnf_pct":      round(dnf_counts[drv] / n_sims * 100, 2),
            "avg_lap_time": round(min(avg_lt, 200), 3),
            "elo":          DRIVERS[drv].elo,
        })

    results.sort(key=lambda x: -x["win_pct"])
    return {"simulations": n_sims, "weather": weather_mode, "laps": track_laps, "drivers": results}


# ─────────────────────────────────────────────────────────────────────────────
#  LIVE RACE ENGINE (threaded)
# ─────────────────────────────────────────────────────────────────────────────

race_state: Optional[RaceState] = None
race_lock = threading.Lock()

def run_live_race(drivers_subset: List[str], total_laps: int, weather: str):
    global race_state
    state = RaceState(total_laps=total_laps, weather=weather)
    state.running = True
    for i, drv in enumerate(drivers_subset):
        state.positions[drv]   = i + 1
        state.lap_times[drv]   = []
        state.gaps[drv]        = 0.0
        state.pit_windows[drv] = {"count": 0, "current_tire": "soft" if i < 10 else "medium", "tire_age": 0}

    cumulative  = {drv: i * 0.5 for i, drv in enumerate(drivers_subset)}
    tire_data   = {drv: {"compound": state.pit_windows[drv]["current_tire"], "age": 0} for drv in drivers_subset}
    active_drv  = list(drivers_subset)

    with race_lock:
        race_state = state

    for lap in range(1, total_laps + 1):
        with race_lock:
            if not race_state or not race_state.running:
                return

        time.sleep(0.35)
        sc_active  = random.random() < 0.03 and 5 < lap < total_laps - 5
        vsc_active = (not sc_active) and random.random() < 0.025

        if random.random() < 0.008:
            with race_lock:
                race_state.weather = "wet" if race_state.weather == "dry" else "dry"
                race_state.strategy_log.append(f"Lap {lap}: Weather change → {race_state.weather.upper()}")

        for drv in active_drv[:]:
            if drv in state.dnf_list:
                continue
            team_obj = TEAMS[DRIVERS[drv].team]
            if random.random() < (1 - team_obj.reliability / 100) * 0.003:
                with race_lock:
                    race_state.dnf_list.append(drv)
                    race_state.strategy_log.append(f"Lap {lap}: 🚨 {DRIVERS[drv].name} DNF — mechanical failure")
                active_drv.remove(drv)
                continue

            td = tire_data[drv]
            td["age"] += 1
            compound  = TIRE_COMPOUNDS[td["compound"]]
            laps_left = total_laps - lap
            fuel_frac = 1.0 - (lap / total_laps)

            with race_lock:
                cur_weather = race_state.weather

            if laps_left > 3 and should_pit(drv, compound, td["age"], laps_left, team_obj.strategy_iq):
                pit_t = compute_pit_time(team_obj)
                cumulative[drv] += pit_t
                old_tire    = td["compound"]
                td["compound"] = "medium" if laps_left > 20 else ("hard" if laps_left > 10 else "soft")
                if cur_weather in ("wet", "damp"):
                    td["compound"] = "inter"
                td["age"] = 0
                with race_lock:
                    race_state.pit_windows[drv]["count"] += 1
                    race_state.pit_windows[drv]["current_tire"] = td["compound"]
                    race_state.pit_windows[drv]["tire_age"]     = 0
                    race_state.strategy_log.append(f"Lap {lap}: 🔧 {DRIVERS[drv].name} pits ({old_tire}→{td['compound']}, {pit_t:.1f}s)")
                compound = TIRE_COMPOUNDS[td["compound"]]

            lap_t, _ = compute_lap_time(drv, compound, td["age"], fuel_frac, cur_weather,
                                         sc_active, vsc_active, random.random() < 0.45)
            cumulative[drv] += lap_t
            with race_lock:
                race_state.lap_times[drv].append(lap_t)
                race_state.pit_windows[drv]["tire_age"]     = td["age"]
                race_state.pit_windows[drv]["current_tire"] = td["compound"]

        sorted_drv = sorted([(d, t) for d, t in cumulative.items() if d not in state.dnf_list], key=lambda x: x[1])
        leader_t   = sorted_drv[0][1] if sorted_drv else 0

        with race_lock:
            for pos, (drv, cum_t) in enumerate(sorted_drv):
                race_state.positions[drv] = pos + 1
                race_state.gaps[drv]      = round(cum_t - leader_t, 3)
            race_state.lap              = lap
            race_state.safety_car_active = sc_active
            race_state.vsc_active        = vsc_active
            if sc_active:
                race_state.strategy_log.append(f"Lap {lap}: 🚗 SAFETY CAR DEPLOYED")
            elif vsc_active:
                race_state.strategy_log.append(f"Lap {lap}: 🟡 VIRTUAL SAFETY CAR")

    with race_lock:
        race_state.running  = False
        race_state.finished = True


# ─────────────────────────────────────────────────────────────────────────────
#  API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/drivers")
def api_drivers():
    out = []
    for did, d in DRIVERS.items():
        t = TEAMS[d.team]
        out.append({"id": did, "name": d.name, "team": d.team, "number": d.number,
                    "skill": d.skill, "consistency": d.consistency, "wet_skill": d.wet_skill,
                    "overtaking": d.overtaking, "tire_mgmt": d.tire_mgmt,
                    "qualifying_pace": d.qualifying_pace, "mental": d.mental,
                    "elo": d.elo, "color": d.color, "team_color": t.color,
                    "car_pace": t.car_pace, "reliability": t.reliability})
    return jsonify(out)

@app.route("/api/teams")
def api_teams():
    return jsonify([{"name": n, "car_pace": t.car_pace, "reliability": t.reliability,
                     "aero_efficiency": t.aero_efficiency, "pit_crew_speed": t.pit_crew_speed,
                     "strategy_iq": t.strategy_iq, "color": t.color} for n, t in TEAMS.items()])

@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    body   = request.json or {}
    n_sims = min(int(body.get("simulations", 1000)), 5000)
    result = monte_carlo_race(n_sims=n_sims, track_laps=int(body.get("laps", 57)),
                               weather_mode=body.get("weather", "dry"),
                               selected_drivers=body.get("drivers", list(DRIVERS.keys())[:20]))
    return jsonify(result)

@app.route("/api/race/start", methods=["POST"])
def api_race_start():
    global race_state
    body = request.json or {}
    with race_lock:
        if race_state and race_state.running:
            return jsonify({"error": "Race already running"}), 409
    t = threading.Thread(target=run_live_race,
                         args=(body.get("drivers", list(DRIVERS.keys())[:10]),
                               int(body.get("laps", 57)), body.get("weather", "dry")), daemon=True)
    t.start()
    return jsonify({"status": "started"})

@app.route("/api/race/stop", methods=["POST"])
def api_race_stop():
    with race_lock:
        if race_state: race_state.running = False
    return jsonify({"status": "stopped"})

@app.route("/api/race/status")
def api_race_status():
    with race_lock:
        if not race_state:
            return jsonify({"status": "idle"})
        pos_list = sorted(race_state.positions.items(), key=lambda x: x[1])
        return jsonify({
            "status":    "finished" if race_state.finished else ("running" if race_state.running else "idle"),
            "lap":       race_state.lap, "total_laps": race_state.total_laps,
            "weather":   race_state.weather, "safety_car": race_state.safety_car_active,
            "vsc":       race_state.vsc_active,
            "positions": [{"driver_id": d, "pos": p,
                           "gap":   race_state.gaps.get(d, 0),
                           "name":  DRIVERS[d].name if d in DRIVERS else d,
                           "team":  DRIVERS[d].team if d in DRIVERS else "",
                           "color": DRIVERS[d].color if d in DRIVERS else "#fff",
                           "tire":  race_state.pit_windows.get(d, {}).get("current_tire", "?"),
                           "tire_age": race_state.pit_windows.get(d, {}).get("tire_age", 0),
                           "pits":  race_state.pit_windows.get(d, {}).get("count", 0),
                           "lap_times": race_state.lap_times.get(d, [])[-5:],
                           "dnf":   d in race_state.dnf_list} for d, p in pos_list],
            "dnf":       race_state.dnf_list,
            "log":       race_state.strategy_log[-30:],
        })

@app.route("/api/qualifying", methods=["POST"])
def api_qualifying():
    body    = request.json or {}
    drivers = body.get("drivers", list(DRIVERS.keys())[:20])
    weather = body.get("weather", "dry")
    results = []
    for drv in drivers:
        d   = DRIVERS[drv]
        wet = (100 - d.wet_skill) * 0.02 if weather == "wet" else 0
        q_t = BASE_LAP_TIME + (100 - d.qualifying_pace) * 0.028 + random.gauss(0, 0.15) + wet
        results.append({"driver_id": drv, "name": d.name, "team": d.team,
                         "color": d.color, "lap_time": round(q_t, 3)})
    results.sort(key=lambda x: x["lap_time"])
    for i, r in enumerate(results):
        r["position"] = i + 1
        r["gap_to_pole"] = round(r["lap_time"] - results[0]["lap_time"], 3)
    return jsonify(results)


# ─────────────────────────────────────────────────────────────────────────────
#  EMBEDDED SINGLE-PAGE FRONTEND
# ─────────────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>F1 RACE ORACLE — SIMULATION ENGINE</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{--red:#e8002d;--gold:#ffd700;--bg:#060a12;--card:rgba(13,20,33,.85);--border:#1a2740;--text:#c8d8e8;--dim:#5a7a9a;--green:#00e676;--yellow:#ffd600;--blue:#4af;--white:#eaf4ff;--glow-red:0 0 25px rgba(232,0,45,.35);--glow-gold:0 0 20px rgba(255,215,0,.25)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'JetBrains Mono',monospace;min-height:100vh;overflow-x:hidden}
#particles{position:fixed;inset:0;z-index:0;pointer-events:none}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 80% 50% at 50% 0%,rgba(232,0,45,.1),transparent 70%),radial-gradient(ellipse 60% 40% at 80% 100%,rgba(255,215,0,.06),transparent 70%),radial-gradient(ellipse 40% 30% at 20% 60%,rgba(68,170,255,.04),transparent);pointer-events:none;z-index:1}
header{position:sticky;top:0;z-index:100;background:rgba(6,10,18,.92);backdrop-filter:blur(16px) saturate(1.4);border-bottom:1px solid var(--border);padding:14px 28px;display:flex;align-items:center;gap:20px}
.logo{font-family:'Orbitron',monospace;font-weight:900;font-size:1.4rem;letter-spacing:.18em;color:var(--white);text-shadow:0 0 30px rgba(232,0,45,.3)}
.logo span{color:var(--red);text-shadow:0 0 20px rgba(232,0,45,.5)}
.status-pill{padding:5px 16px;border-radius:3px;font-size:.7rem;font-weight:600;letter-spacing:.12em;border:1px solid currentColor;backdrop-filter:blur(6px)}
.pill-idle{color:var(--dim);border-color:var(--border)}
.pill-running{color:var(--green);border-color:var(--green);animation:pulse 1.2s ease infinite;box-shadow:0 0 12px rgba(0,230,118,.2)}
.pill-finished{color:var(--gold);border-color:var(--gold);box-shadow:var(--glow-gold)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
@keyframes slideIn{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:translateX(0)}}
@keyframes glow{0%,100%{box-shadow:0 0 5px rgba(232,0,45,.2)}50%{box-shadow:0 0 20px rgba(232,0,45,.4)}}
.lap-counter{margin-left:auto;font-family:'Orbitron',monospace;font-size:.9rem;color:var(--gold);text-shadow:var(--glow-gold)}
.grid{display:grid;grid-template-columns:320px 1fr;gap:0;height:calc(100vh - 57px);position:relative;z-index:2}
.sidebar{border-right:1px solid var(--border);overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;background:rgba(6,10,18,.5);backdrop-filter:blur(8px)}
.main{overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
.card{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:16px;position:relative;backdrop-filter:blur(12px);transition:border-color .3s,box-shadow .3s}
.card:hover{border-color:#2a3d5a;box-shadow:0 4px 24px rgba(0,0,0,.3)}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--red),var(--gold),transparent);border-radius:6px 6px 0 0}
.card-title{font-family:'Orbitron',monospace;font-size:.65rem;letter-spacing:.2em;color:var(--dim);margin-bottom:12px;text-transform:uppercase}
.btn{display:block;width:100%;padding:11px 0;font-family:'Orbitron',monospace;font-size:.72rem;letter-spacing:.15em;font-weight:700;border:1px solid;border-radius:3px;cursor:pointer;transition:all .25s ease;text-transform:uppercase;background:transparent;position:relative;overflow:hidden}
.btn::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.05),transparent);transform:translateX(-100%);transition:transform .5s}
.btn:hover::after{transform:translateX(100%)}
.btn-primary{color:var(--red);border-color:var(--red)}
.btn-primary:hover{background:var(--red);color:#fff;box-shadow:var(--glow-red);transform:translateY(-1px)}
.btn-secondary{color:var(--blue);border-color:var(--blue)}
.btn-secondary:hover{background:rgba(68,170,255,.15);box-shadow:0 0 15px rgba(68,170,255,.2);transform:translateY(-1px)}
.btn-warn{color:var(--yellow);border-color:var(--yellow)}
.btn-warn:hover{background:rgba(255,214,0,.15);box-shadow:0 0 15px rgba(255,214,0,.2);transform:translateY(-1px)}
.btn-sm{padding:6px 12px;font-size:.63rem;width:auto;display:inline-block}
select,input[type=number]{width:100%;background:rgba(255,255,255,.04);border:1px solid var(--border);color:var(--text);padding:7px 10px;border-radius:3px;font-family:'JetBrains Mono',monospace;font-size:.78rem;outline:none;margin-top:4px;transition:border-color .2s,box-shadow .2s}
select:focus,input:focus{border-color:var(--red);box-shadow:0 0 8px rgba(232,0,45,.15)}
label{font-size:.7rem;color:var(--dim);display:block;margin-top:8px;letter-spacing:.05em}
.driver-row{display:flex;align-items:center;gap:8px;padding:6px 4px;border-bottom:1px solid rgba(255,255,255,.04);cursor:pointer;transition:all .2s ease;border-radius:3px}
.driver-row:hover{background:rgba(255,255,255,.04);padding-left:8px;border-color:rgba(255,255,255,.08)}
.drv-num{font-family:'Orbitron',monospace;font-size:.75rem;font-weight:700;width:26px;text-align:center;flex-shrink:0}
.drv-name{font-size:.75rem;flex:1;color:var(--white)}
.drv-team{font-size:.62rem;color:var(--dim)}
.chk{width:15px;height:15px;border:1px solid var(--border);border-radius:3px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s;font-size:.6rem}
.chk.on{background:var(--red);border-color:var(--red);color:white;box-shadow:0 0 8px rgba(232,0,45,.3)}
.race-row{display:grid;grid-template-columns:28px 10px 1fr 56px 70px 42px 72px;gap:6px;align-items:center;padding:6px 8px;border-radius:4px;transition:all .25s ease;animation:fadeIn .3s ease}
.race-row:hover{background:rgba(255,255,255,.04)}
.race-row.leader{background:rgba(255,215,0,.07);border-left:3px solid var(--gold);box-shadow:inset 0 0 20px rgba(255,215,0,.03)}
.pos-num{font-family:'Orbitron',monospace;font-weight:700;color:var(--dim);text-align:center;font-size:.78rem}
.gap-col{color:var(--dim);text-align:right;font-size:.68rem}
.tire-badge{padding:3px 8px;border-radius:3px;font-size:.62rem;font-weight:700;letter-spacing:.05em}
.tire-S{background:#ff1e1e18;color:#ff5555;border:1px solid #ff1e1e44}
.tire-M{background:#ffd70018;color:#ffd700;border:1px solid #ffd70044}
.tire-H{background:#e8e8e818;color:#e0e0e0;border:1px solid #e8e8e844}
.tire-I{background:#39b54a18;color:#39b54a;border:1px solid #39b54a44}
.tire-W{background:#0067ff18;color:#0067ff;border:1px solid #0067ff44}
.pits-col{color:var(--dim);text-align:center;font-size:.65rem}
.dnf-tag{color:var(--red);font-size:.65rem;font-weight:700;text-shadow:0 0 8px rgba(232,0,45,.3)}
.log-box{font-size:.68rem;line-height:1.9;max-height:280px;overflow-y:auto;color:var(--dim);padding:4px 0}
.log-box span{display:block;padding:1px 0;border-bottom:1px solid rgba(255,255,255,.02)}
.log-box .warn{color:var(--yellow)}
.log-box .danger{color:var(--red)}
.log-box .info{color:var(--green)}
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);margin-bottom:12px}
.tab{padding:8px 18px;font-family:'Orbitron',monospace;font-size:.63rem;letter-spacing:.12em;cursor:pointer;color:var(--dim);border-bottom:2px solid transparent;transition:all .25s}
.tab:hover{color:var(--text)}
.tab.active{color:var(--white);border-color:var(--red);text-shadow:0 0 10px rgba(232,0,45,.3)}
.tab-content{display:none}
.tab-content.active{display:block;animation:fadeIn .3s ease}
.bar-wrap{margin:4px 0}
.bar-label{display:flex;justify-content:space-between;font-size:.68rem;margin-bottom:3px}
.bar{height:7px;border-radius:2px;overflow:hidden;background:rgba(255,255,255,.06)}
.bar-fill{height:100%;border-radius:2px;transition:width .6s ease}
.chart-wrap{position:relative;height:260px}
.weather-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 14px;border-radius:3px;font-size:.7rem;font-weight:600;border:1px solid;backdrop-filter:blur(4px)}
.weather-dry{color:#ffd700;border-color:#ffd70055;background:#ffd70010}
.weather-wet{color:#4af;border-color:#4af5;background:#4af1}
.weather-damp{color:#39b54a;border-color:#39b54a55;background:#39b54a10}
.sc-banner{background:rgba(255,214,0,.1);border:1px solid var(--yellow);border-radius:4px;padding:10px 16px;font-family:'Orbitron',monospace;font-size:.72rem;color:var(--yellow);display:none;animation:glow 1.5s ease infinite;text-align:center;backdrop-filter:blur(6px)}
.vsc-banner{background:rgba(255,152,0,.08);border:1px solid #ff9800;border-radius:4px;padding:10px 16px;font-family:'Orbitron',monospace;font-size:.72rem;color:#ff9800;display:none;animation:pulse 1.5s ease infinite;text-align:center;backdrop-filter:blur(6px)}
.progress-wrap{background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden;height:8px;box-shadow:inset 0 1px 3px rgba(0,0,0,.3)}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--red),var(--gold));transition:width .5s ease;border-radius:3px;box-shadow:0 0 10px rgba(232,0,45,.3)}
.row-header{display:grid;grid-template-columns:28px 10px 1fr 56px 70px 42px 72px;gap:6px;padding:4px 6px;font-size:.58rem;color:var(--dim);letter-spacing:.12em;border-bottom:1px solid var(--border);margin-bottom:4px;text-transform:uppercase}
.qual-row{display:grid;grid-template-columns:28px 10px 1fr 100px 80px;gap:6px;align-items:center;padding:6px 8px;border-radius:4px;font-size:.72rem;transition:all .2s;animation:fadeIn .3s ease}
.qual-row:hover{background:rgba(255,255,255,.04)}
.loader{text-align:center;padding:30px;color:var(--dim);font-size:.78rem;animation:pulse .8s ease infinite}
.pos-up{color:var(--green);font-size:.55rem;margin-left:2px}
.pos-down{color:var(--red);font-size:.55rem;margin-left:2px}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#2a3d5a}
</style>
</head>
<body>
<canvas id="particles"></canvas>
<header>
  <div class="logo">F1 <span>ORACLE</span></div>
  <div id="statusPill" class="status-pill pill-idle">IDLE</div>
  <div id="weatherBadge" class="weather-badge weather-dry">☀ DRY</div>
  <div id="lapCounter" class="lap-counter">LAP —/—</div>
</header>

<div class="grid">
<div class="sidebar">
  <div class="card">
    <div class="card-title">Race Configuration</div>
    <label>CIRCUIT LAPS</label>
    <input type="number" id="cfgLaps" value="57" min="10" max="78">
    <label>WEATHER CONDITIONS</label>
    <select id="cfgWeather">
      <option value="dry">☀ Dry — Full slick pace</option>
      <option value="wet">🌧 Wet — Aquaplaning risk</option>
      <option value="damp">🌦 Damp — Mixed conditions</option>
      <option value="random">🎲 Dynamic — Unpredictable</option>
    </select>
    <label>MONTE CARLO ITERATIONS</label>
    <select id="cfgSims">
      <option value="500">500 — Quick</option>
      <option value="1000" selected>1,000 — Standard</option>
      <option value="2000">2,000 — Accurate</option>
      <option value="5000">5,000 — High Precision</option>
    </select>
    <div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:8px">
      <button class="btn btn-primary btn-sm" onclick="runMonteCarlo()">▶ SIMULATE</button>
      <button class="btn btn-secondary btn-sm" onclick="runQualifying()">⚡ QUALIFYING</button>
    </div>
    <div style="height:8px"></div>
    <button class="btn btn-primary" onclick="startLiveRace()" id="btnStart">▶ START LIVE RACE</button>
    <button class="btn btn-warn" onclick="stopRace()" id="btnStop" style="display:none;margin-top:6px">■ STOP RACE</button>
  </div>

  <div class="card">
    <div class="card-title">Driver Selection <span id="selCount" style="color:var(--blue)">(0)</span></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px">
      <button class="btn btn-secondary btn-sm" onclick="selAll()">ALL 20</button>
      <button class="btn btn-warn btn-sm" onclick="selTop10()">TOP 10</button>
    </div>
    <div id="driverList"></div>
  </div>
</div>

<div class="main">
  <div id="scBanner" class="sc-banner">⚠ SAFETY CAR DEPLOYED</div>
  <div id="vscBanner" class="vsc-banner">🟡 VIRTUAL SAFETY CAR ACTIVE</div>
  <div class="progress-wrap"><div class="progress-fill" id="raceProgress" style="width:0%"></div></div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('live')">LIVE RACE</div>
    <div class="tab" onclick="switchTab('montecarlo')">MONTE CARLO</div>
    <div class="tab" onclick="switchTab('qualifying')">QUALIFYING</div>
    <div class="tab" onclick="switchTab('drivers')">DRIVER STATS</div>
    <div class="tab" onclick="switchTab('strategy')">STRATEGY LOG</div>
  </div>

  <div id="tab-live" class="tab-content active">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="card" style="grid-column:1/-1">
        <div class="card-title">Race Standings</div>
        <div class="row-header"><span>POS</span><span></span><span>DRIVER</span><span>TIRE</span><span>GAP</span><span>PIT</span><span>LAST LAP</span></div>
        <div id="raceStandings"><div style="color:var(--dim);font-size:.75rem;padding:20px;text-align:center">Select drivers and press START LIVE RACE</div></div>
      </div>
      <div class="card">
        <div class="card-title">Lap Time Trend — Top 5</div>
        <div class="chart-wrap"><canvas id="lapChart"></canvas></div>
      </div>
      <div class="card">
        <div class="card-title">Gap to Leader</div>
        <div id="gapBars"><div style="color:var(--dim);font-size:.7rem;padding:10px">Race not started</div></div>
      </div>
    </div>
  </div>

  <div id="tab-montecarlo" class="tab-content">
    <div id="mcLoader" class="loader" style="display:none">⟳ Running Monte Carlo simulations...</div>
    <div id="mcResults"><div style="color:var(--dim);font-size:.75rem;padding:20px;text-align:center">Configure settings and press SIMULATE</div></div>
  </div>

  <div id="tab-qualifying" class="tab-content">
    <div id="qualLoader" class="loader" style="display:none">⟳ Running qualifying simulation...</div>
    <div id="qualResults"><div style="color:var(--dim);font-size:.75rem;padding:20px;text-align:center">Press QUALIFYING to run a session</div></div>
  </div>

  <div id="tab-drivers" class="tab-content">
    <div id="driverStats"></div>
  </div>

  <div id="tab-strategy" class="tab-content">
    <div class="card">
      <div class="card-title">Race Strategy & Events Log</div>
      <div class="log-box" id="fullLog"><span style="color:var(--dim)">Awaiting race start...</span></div>
    </div>
  </div>
</div>
</div>

<script>
let selectedDrivers=new Set(),allDrivers=[],lapChart=null,pollTimer=null;

async function fetchDrivers(){
  try {
    const r=await fetch('/api/drivers');
    allDrivers=await r.json();
    renderDriverList();
    renderDriverStats();
    selTop10();
  } catch (e) {
    console.error("Error fetching drivers", e);
  }
}

function renderDriverList(){
  document.getElementById('driverList').innerHTML=allDrivers.map(d=>`
    <div class="driver-row" onclick="toggleDriver('${d.id}')">
      <div class="drv-num" style="color:${d.color}">${d.number}</div>
      <div style="width:8px;height:8px;border-radius:50%;background:${d.color};flex-shrink:0"></div>
      <div><div class="drv-name">${d.name}</div><div class="drv-team">${d.team}</div></div>
      <div class="chk ${selectedDrivers.has(d.id)?'on':''}" id="chk_${d.id}">${selectedDrivers.has(d.id)?'✓':''}</div>
    </div>`).join('');
}

function toggleDriver(id){
  if(selectedDrivers.has(id)){selectedDrivers.delete(id);}else{selectedDrivers.add(id);}
  const c=document.getElementById('chk_'+id);
  c.className='chk '+(selectedDrivers.has(id)?'on':'');
  c.textContent=selectedDrivers.has(id)?'✓':'';
  document.getElementById('selCount').textContent=`(${selectedDrivers.size})`;
}

function selAll(){selectedDrivers=new Set(allDrivers.map(d=>d.id));renderDriverList();document.getElementById('selCount').textContent=`(${selectedDrivers.size})`}
function selTop10(){selectedDrivers=new Set(allDrivers.slice(0,10).map(d=>d.id));renderDriverList();document.getElementById('selCount').textContent=`(${selectedDrivers.size})`}

function switchTab(name){
  const names=['live','montecarlo','qualifying','drivers','strategy'];
  document.querySelectorAll('.tab').forEach((t,i)=>{t.className='tab'+(names[i]===name?' active':'')});
  document.querySelectorAll('.tab-content').forEach(t=>t.className='tab-content');
  document.getElementById('tab-'+name).className='tab-content active';
}

async function runMonteCarlo(){
  if(selectedDrivers.size<2){alert('Select at least 2 drivers');return;}
  switchTab('montecarlo');
  document.getElementById('mcLoader').style.display='block';
  document.getElementById('mcResults').innerHTML='';
  try {
    const r=await fetch('/api/simulate',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({simulations:+document.getElementById('cfgSims').value,
        laps:+document.getElementById('cfgLaps').value,
        weather:document.getElementById('cfgWeather').value,
        drivers:[...selectedDrivers]})});
    const data=await r.json();
    document.getElementById('mcLoader').style.display='none';
    renderMC(data);
  } catch (e) {
    document.getElementById('mcLoader').style.display='none';
    document.getElementById('mcResults').innerHTML='<div style="color:var(--red);padding:20px;">Error running simulation.</div>';
  }
}

function renderMC(data){
  if (!data || !data.drivers) return;
  const max=data.drivers[0]?.win_pct||1;
  let html=`<div class="card"><div class="card-title">Monte Carlo — ${data.simulations.toLocaleString()} Simulations | ${data.weather.toUpperCase()} | ${data.laps} Laps</div>
  <div style="display:grid;grid-template-columns:28px 10px 1fr 85px 85px 70px 70px 65px;gap:6px;font-size:.58rem;color:var(--dim);padding:4px 6px;border-bottom:1px solid var(--border);margin-bottom:6px;letter-spacing:.08em">
    <span>POS</span><span></span><span>DRIVER</span><span>WIN %</span><span>PODIUM %</span><span>AVG FIN</span><span>AVG PTS</span><span>DNF %</span>
  </div>`;
  data.drivers.forEach((d,i)=>{
    const w=d.win_pct/max*100;
    const posColor=i<3?['#ffd700','#c0c0c0','#cd7f32'][i]:'var(--dim)';
    html+=`<div style="display:grid;grid-template-columns:28px 10px 1fr 85px 85px 70px 70px 65px;gap:6px;align-items:center;padding:5px 6px;border-radius:3px" onmouseover="this.style.background='rgba(255,255,255,.03)'" onmouseout="this.style.background=''">
      <span style="font-family:'Orbitron',monospace;font-size:.75rem;color:${posColor};text-align:center;font-weight:700">${i+1}</span>
      <div style="width:8px;height:8px;border-radius:50%;background:${d.color}"></div>
      <div>
        <div style="font-size:.73rem;color:var(--white)">${d.name}</div>
        <div style="font-size:.6rem;color:var(--dim)">${d.team}</div>
        <div style="height:4px;background:rgba(255,255,255,.06);border-radius:1px;margin-top:3px;overflow:hidden">
          <div style="height:100%;width:${w}%;background:${d.color};border-radius:1px;transition:width 1s"></div></div>
      </div>
      <div style="font-size:.78rem;color:${d.win_pct>30?d.color:'var(--text)'};font-weight:600">${d.win_pct}%</div>
      <div style="font-size:.72rem;color:${d.podium_pct>40?'var(--green)':'var(--text)'}">${d.podium_pct}%</div>
      <div style="font-size:.72rem;color:var(--dim)">${d.avg_finish}</div>
      <div style="font-size:.72rem;color:var(--gold)">${d.avg_points}</div>
      <div style="font-size:.72rem;color:${d.dnf_pct>8?'var(--red)':'var(--dim)'}">${d.dnf_pct}%</div>
    </div>`;
  });
  html+='</div>';
  const top8=data.drivers.slice(0,Math.min(8,data.drivers.length));
  html+=`<div class="card"><div class="card-title">Win Probability Chart</div><div class="chart-wrap"><canvas id="mcChart"></canvas></div></div>`;
  document.getElementById('mcResults').innerHTML=html;
  new Chart(document.getElementById('mcChart'),{type:'bar',
    data:{labels:top8.map(d=>d.name.split(' ').pop()),
      datasets:[
        {label:'Win %',data:top8.map(d=>d.win_pct),backgroundColor:top8.map(d=>d.color+'cc'),borderColor:top8.map(d=>d.color),borderWidth:1,borderRadius:3},
        {label:'Podium %',data:top8.map(d=>d.podium_pct),backgroundColor:top8.map(d=>d.color+'40'),borderColor:top8.map(d=>d.color+'88'),borderWidth:1,borderRadius:3}
      ]},
    options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{labels:{color:'#5a7a9a',font:{family:'JetBrains Mono',size:10},boxWidth:10}}},
      scales:{x:{ticks:{color:'#5a7a9a',font:{family:'JetBrains Mono',size:10}},grid:{color:'rgba(255,255,255,.04)'}},
              y:{ticks:{color:'#5a7a9a',font:{family:'JetBrains Mono',size:10}},grid:{color:'rgba(255,255,255,.04)'}}}}});
}

async function runQualifying(){
  if(selectedDrivers.size<2){alert('Select at least 2 drivers');return;}
  switchTab('qualifying');
  document.getElementById('qualLoader').style.display='block';
  document.getElementById('qualResults').innerHTML='';
  try {
    const r=await fetch('/api/qualifying',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({drivers:[...selectedDrivers],weather:document.getElementById('cfgWeather').value})});
    const data=await r.json();
    document.getElementById('qualLoader').style.display='none';
    let html=`<div class="card"><div class="card-title">Qualifying Classification</div>
    <div style="display:grid;grid-template-columns:28px 10px 1fr 110px 90px;gap:6px;font-size:.58rem;color:var(--dim);padding:4px 6px;border-bottom:1px solid var(--border);margin-bottom:6px;letter-spacing:.08em">
      <span>POS</span><span></span><span>DRIVER</span><span>LAP TIME</span><span>GAP</span>
    </div>`;
    data.forEach((d,i)=>{
      const m=Math.floor(d.lap_time/60);
      const s=(d.lap_time%60).toFixed(3).padStart(6,'0');
      const posC=i<3?['#ffd700','#c0c0c0','#cd7f32'][i]:'var(--dim)';
      html+=`<div class="qual-row">
        <span style="font-family:'Orbitron',monospace;font-weight:700;color:${posC};text-align:center">${i+1}</span>
        <div style="width:8px;height:8px;border-radius:50%;background:${d.color}"></div>
        <div><div style="font-size:.75rem;color:var(--white)">${d.name}</div><div style="font-size:.62rem;color:var(--dim)">${d.team}</div></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:.8rem;color:${i===0?'var(--gold)':'var(--text)'}">${m}:${s}</span>
        <span style="color:var(--dim);font-size:.7rem">${i===0?'◆ POLE':'+'+d.gap_to_pole.toFixed(3)+'s'}</span>
      </div>`;
    });
    html+='</div>';
    document.getElementById('qualResults').innerHTML=html;
  } catch (e) {
    document.getElementById('qualLoader').style.display='none';
    document.getElementById('qualResults').innerHTML='<div style="color:var(--red);padding:20px;">Error running qualifying.</div>';
  }
}

function renderDriverStats(){
  let html='<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:10px">';
  allDrivers.forEach(d=>{
    const stats=[
      {k:'DRIVER SKILL',v:d.skill},{k:'CONSISTENCY',v:d.consistency},{k:'WET SKILL',v:d.wet_skill},
      {k:'OVERTAKING',v:d.overtaking},{k:'TIRE MANAGEMENT',v:d.tire_mgmt},{k:'CAR PACE',v:d.car_pace},{k:'MENTAL STRENGTH',v:d.mental}
    ];
    html+=`<div class="card"><div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
      <div style="width:28px;height:28px;border-radius:50%;background:${d.color}22;border:2px solid ${d.color};display:flex;align-items:center;justify-content:center;font-family:'Orbitron',monospace;font-size:.65rem;font-weight:700;color:${d.color}">${d.number}</div>
      <div style="flex:1"><div style="font-family:'Orbitron',monospace;font-size:.75rem;color:var(--white)">${d.name}</div>
      <div style="font-size:.62rem;color:var(--dim)">${d.team}</div></div>
      <div style="text-align:right"><div style="font-size:.6rem;color:var(--dim)">ELO</div><div style="font-family:'Orbitron',monospace;font-size:.78rem;color:var(--gold)">${d.elo}</div></div>
    </div>`;
    stats.forEach(s=>{
      const barColor=s.v>=90?'#00e676':s.v>=80?d.color:s.v>=70?'#ffd600':'#e8002d';
      html+=`<div class="bar-wrap"><div class="bar-label"><span style="font-size:.62rem;color:var(--dim)">${s.k}</span><span style="font-size:.62rem;color:${barColor};font-weight:600">${s.v}</span></div>
        <div class="bar"><div class="bar-fill" style="width:${s.v}%;background:${barColor}88"></div></div></div>`;
    });
    html+='</div>';
  });
  html+='</div>';
  document.getElementById('driverStats').innerHTML=html;
}

async function startLiveRace(){
  if(selectedDrivers.size<2){alert('Select at least 2 drivers');return;}
  try {
    await fetch('/api/race/start',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({drivers:[...selectedDrivers],laps:+document.getElementById('cfgLaps').value,
        weather:document.getElementById('cfgWeather').value})});
    document.getElementById('btnStart').style.display='none';
    document.getElementById('btnStop').style.display='block';
    document.getElementById('statusPill').className='status-pill pill-running';
    document.getElementById('statusPill').textContent='RACING';
    switchTab('live');
    if(lapChart){lapChart.destroy();lapChart=null;}
    pollTimer=setInterval(pollRace,700);
  } catch (e) {
    alert("Failed to start race: " + e.message);
  }
}

async function stopRace(){
  try {
    await fetch('/api/race/stop',{method:'POST'});
    clearInterval(pollTimer);
    document.getElementById('btnStart').style.display='block';
    document.getElementById('btnStop').style.display='none';
    document.getElementById('statusPill').className='status-pill pill-idle';
    document.getElementById('statusPill').textContent='IDLE';
  } catch (e) {
    console.error("Failed to stop race", e);
  }
}

async function pollRace(){
  try{
    const r=await fetch('/api/race/status');
    const data=await r.json();
    if(data.status==='idle')return;
    const pill=document.getElementById('statusPill');
    if(data.status==='finished'){
      clearInterval(pollTimer);
      pill.className='status-pill pill-finished';
      pill.textContent='FINISHED';
      document.getElementById('btnStart').style.display='block';
      document.getElementById('btnStop').style.display='none';
    }
    document.getElementById('lapCounter').textContent=`LAP ${data.lap}/${data.total_laps}`;
    document.getElementById('raceProgress').style.width=`${(data.lap/data.total_laps)*100}%`;
    const wb=document.getElementById('weatherBadge');
    wb.className='weather-badge weather-'+data.weather;
    wb.innerHTML={dry:'☀ DRY',wet:'🌧 WET',damp:'🌦 DAMP'}[data.weather]||'☀ DRY';
    document.getElementById('scBanner').style.display=data.safety_car?'block':'none';
    document.getElementById('vscBanner').style.display=data.vsc?'block':'none';

    // Standings
    let rows='';
    data.positions.forEach((p,i)=>{
      if(p.dnf){
        rows+=`<div class="race-row"><span class="pos-num" style="color:var(--red)">DNF</span>
          <div style="width:8px;height:8px;border-radius:50%;background:${p.color}"></div>
          <div><div style="font-size:.72rem;color:var(--dim);text-decoration:line-through">${p.name}</div><div style="font-size:.6rem;color:var(--dim)">${p.team}</div></div>
          <span class="dnf-tag">DNF</span><span></span><span></span><span></span></div>`;
        return;
      }
      const tc=(p.tire||'?')[0].toUpperCase();
      const lt=p.lap_times.length?p.lap_times[p.lap_times.length-1].toFixed(3):'—';
      const gapTxt=i===0?'LEADER':('+'+p.gap.toFixed(3)+'s');
      const posC=p.pos<=3?['#ffd700','#c0c0c0','#cd7f32'][p.pos-1]:'var(--dim)';
      rows+=`<div class="race-row ${i===0?'leader':''}">
        <span class="pos-num" style="color:${posC}">${p.pos}</span>
        <div style="width:8px;height:8px;border-radius:50%;background:${p.color}"></div>
        <div><div style="font-size:.73rem;color:var(--white)">${p.name}</div><div style="font-size:.6rem;color:var(--dim)">${p.team}</div></div>
        <span class="tire-badge tire-${tc}">${tc}<span style="opacity:.7;font-size:.58rem"> ${p.tire_age}L</span></span>
        <span class="gap-col">${gapTxt}</span>
        <span class="pits-col">${p.pits}🔧</span>
        <span style="font-size:.7rem;color:var(--gold);text-align:right">${lt}</span>
      </div>`;
    });
    document.getElementById('raceStandings').innerHTML=rows;

    // Gap bars
    const active=data.positions.filter(p=>!p.dnf).slice(0,8);
    const maxGap=active.length>1?Math.max(...active.map(p=>p.gap))||1:1;
    document.getElementById('gapBars').innerHTML=active.map(p=>`
      <div class="bar-wrap"><div class="bar-label">
        <span style="font-size:.66rem;color:${p.color}">${p.name.split(' ').pop()}</span>
        <span style="font-size:.66rem;color:var(--dim)">${p.gap===0?'LEADER':'+'+p.gap.toFixed(3)+'s'}</span>
      </div>
      <div class="bar"><div class="bar-fill" style="width:${Math.max(2,p.gap===0?1:Math.min(100,p.gap/maxGap*100))}%;background:${p.color}"></div></div></div>`).join('');

    // Lap time chart
    const top5=data.positions.filter(p=>!p.dnf&&p.lap_times.length>0).slice(0,5);
    const labels=top5[0]?.lap_times.map((_,i)=>`-${5-i}`)??[];
    const ds=top5.map(d=>({label:d.name.split(' ').pop(),data:d.lap_times,borderColor:d.color,
      backgroundColor:d.color+'22',borderWidth:1.5,pointRadius:3,tension:.3}));
    if(!lapChart){
      lapChart=new Chart(document.getElementById('lapChart'),{type:'line',data:{labels,datasets:ds},
        options:{responsive:true,maintainAspectRatio:false,animation:{duration:0},
          plugins:{legend:{labels:{color:'#5a7a9a',font:{family:'JetBrains Mono',size:10},boxWidth:10}}},
          scales:{x:{ticks:{color:'#5a7a9a',font:{size:9}},grid:{color:'rgba(255,255,255,.04)'}},
                  y:{ticks:{color:'#5a7a9a',font:{size:9}},grid:{color:'rgba(255,255,255,.04)'}}}}});
    } else {
      lapChart.data.labels=labels;lapChart.data.datasets=ds;lapChart.update('none');
    }

    // Strategy log
    const log=document.getElementById('fullLog');
    log.innerHTML=data.log.map(l=>{
      const cls=l.includes('🚨')?'danger':l.includes('SAFETY')||l.includes('VSC')||l.includes('Weather')?'warn':l.includes('🔧')?'info':'';
      return`<span class="${cls}">${l}</span>`;
    }).join('');
    log.scrollTop=log.scrollHeight;
  }catch(e){console.error(e);}
}

// ── Particle Background ──
(function(){
  const c=document.getElementById('particles'),ctx=c.getContext('2d');
  let w,h,pts=[];
  function resize(){w=c.width=window.innerWidth;h=c.height=window.innerHeight;pts=[];
    for(let i=0;i<60;i++)pts.push({x:Math.random()*w,y:Math.random()*h,r:Math.random()*1.5+.3,
      dx:(Math.random()-.5)*.3,dy:(Math.random()-.5)*.3,a:Math.random()*.4+.1});}
  function draw(){ctx.clearRect(0,0,w,h);
    pts.forEach(p=>{p.x+=p.dx;p.y+=p.dy;
      if(p.x<0)p.x=w;if(p.x>w)p.x=0;if(p.y<0)p.y=h;if(p.y>h)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(232,0,45,${p.a})`;ctx.fill();});
    requestAnimationFrame(draw);}
  window.addEventListener('resize',resize);resize();draw();
})();

fetchDrivers();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║         F1 RACE ORACLE — SIMULATION ENGINE v1.0             ║
╠══════════════════════════════════════════════════════════════╣
║  ► Open http://localhost:8001 in your browser               ║
║  ► 20 real 2024 F1 drivers with full physics profiles       ║
║  ► Monte Carlo engine: up to 5,000 simulations              ║
║  ► Live race: lap-by-lap with tire/fuel/weather physics     ║
║  ► Features: DRS | Safety Car | VSC | Tire Degradation      ║
║              Pit Strategy | Overtaking | DNF Simulation     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=False, port=8001, threaded=True)
