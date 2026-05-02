# 🏎️ F1 Race Oracle — Simulation Engine

A **high-fidelity Formula 1 race simulation** with Monte Carlo analysis, live race mode, qualifying simulation, and a premium dark-themed dashboard — all in a single Python file.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Monte Carlo Engine** | Up to 5,000 race simulations with stochastic modeling |
| **Live Race Mode** | Lap-by-lap race simulation with real-time position updates |
| **Qualifying Sim** | Single-lap qualifying with weather adjustments |
| **20 Real Drivers** | Full 2024 F1 grid with skill profiles (pace, consistency, wet skill, tire management, etc.) |
| **Tire Physics** | Non-linear degradation with cliff effects for Soft/Medium/Hard/Inter/Wet compounds |
| **Pit Strategy AI** | Dynamic pit decisions based on tire age, laps remaining & team strategy IQ |
| **Safety Car / VSC** | Stochastic Safety Car and Virtual Safety Car events |
| **DRS Simulation** | Drag Reduction System effect on lap times |
| **Weather System** | Dry / Wet / Damp / Dynamic weather with grip adjustments |
| **DNF Modeling** | Mechanical reliability failures based on team reliability ratings |
| **Premium Dashboard** | Glassmorphism UI with particle background, Orbitron typography, and Chart.js visuals |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/f1-race-oracle.git
cd f1-race-oracle

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 claudefastf1_app.py
```

### Open in Browser
Navigate to **http://localhost:8001** — the entire dashboard is self-contained.

---

## 🎮 How to Use

### Monte Carlo Simulation
1. Select drivers from the sidebar (use **ALL 20** or **TOP 10** presets)
2. Configure laps, weather, and iteration count
3. Click **▶ SIMULATE** → view win probabilities, podium %, and bar charts

### Live Race
1. Select your drivers
2. Click **▶ START LIVE RACE**
3. Watch real-time position changes, tire strategies, pit stops, and safety car events
4. Check the **STRATEGY LOG** tab for a full event feed

### Qualifying
1. Click **⚡ QUALIFYING** to run a single-lap session
2. View grid positions with gap-to-pole times

---

## 🏗️ Architecture

The entire application is a **single-file Flask server** (`claudefastf1_app.py`) with:

```
claudefastf1_app.py
├── Data Layer         → 20 driver profiles, 10 team profiles, 5 tire compounds
├── Physics Engine     → Lap time calculation (tire deg, fuel, weather, DRS, SC)
├── Monte Carlo Engine → Batch race simulation with statistical aggregation
├── Live Race Engine   → Threaded lap-by-lap race with real-time state updates
├── API Routes         → RESTful JSON endpoints (/api/drivers, /api/simulate, etc.)
└── Embedded Frontend  → Full HTML/CSS/JS dashboard with Chart.js
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/drivers` | All 20 driver profiles with stats |
| `GET` | `/api/teams` | All 10 team profiles |
| `POST` | `/api/simulate` | Run Monte Carlo simulation |
| `POST` | `/api/qualifying` | Run qualifying session |
| `POST` | `/api/race/start` | Start a live race |
| `POST` | `/api/race/stop` | Stop the live race |
| `GET` | `/api/race/status` | Poll live race state |

---

## 📊 Physics Model

- **Lap Time** = Base + Car Δ + Driver Δ + Tire Δ + Fuel Δ + Weather Δ + DRS Δ + SC Δ + Noise
- **Tire Degradation** = Linear wear + Cliff effect (exponential after cliff lap)
- **Fuel Effect** = 3.85s per unit of fuel load (burns linearly)
- **DRS Gain** = -0.30s when within 0.8s of car ahead
- **Safety Car** = +25s delta, VSC = +8s delta

---

## 🛠️ Tech Stack

- **Backend**: Python 3 + Flask
- **Frontend**: Vanilla HTML/CSS/JS (embedded in Python)
- **Charts**: Chart.js 4.x (loaded via CDN)
- **Fonts**: Orbitron + JetBrains Mono (Google Fonts CDN)

---

## 📁 Project Structure

```
f1-race-oracle/
├── claudefastf1_app.py   # Main application (backend + frontend)
├── requirements.txt      # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

---

## 📜 License

MIT License — feel free to fork, modify, and use in your own projects.

---

**Built with ❤️ and racing passion by Mohammed Khadir Khadri JK**
