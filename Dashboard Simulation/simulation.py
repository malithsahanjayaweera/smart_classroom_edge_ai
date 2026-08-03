import random
from flask import Flask, jsonify, render_template

app = Flask(__name__)
# Enable CORS for external frontends or local clients
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return response
# Simulation States Configuration
POSSIBLE_STATES = [
    {
        "occupancy": "LOW (0-2)",
        "ac_state": "OFF",
        "temp": "--",
        "color": "#94a3b8",
        "base_confidence": 98.2,
        "human_count": 1
    },
    {
        "occupancy": "MEDIUM (3-9)",
        "ac_state": "ON",
        "temp": "24°C",
        "color": "#fbbf24",
        "base_confidence": 95.4,
        "human_count": 6
    },
    {
        "occupancy": "HIGH (10 or higher)",
        "ac_state": "ON",
        "temp": "20°C",
        "color": "#f87171",
        "base_confidence": 97.1,
        "human_count": 14
    }
]
# Track current simulated state
current_state_idx = 0


@app.route("/", methods=["GET"])
def home():
    return render_template("dashboard.html")
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "mode": "simulation"})
@app.route("/api/simulate", methods=["GET"])
def simulate():
    global current_state_idx
    # Randomly decide whether to keep state or shift state (75% stay, 25% shift)
    if random.random() < 0.25:
        # Move to a different state randomly
        other_indices = [i for i in range(len(POSSIBLE_STATES)) if i != current_state_idx]
        current_state_idx = random.choice(other_indices)
    state = dict(POSSIBLE_STATES[current_state_idx])
    # Add slight confidence jitter
    jitter = round(random.uniform(-1.5, 1.5), 1)
    state["confidence"] = min(100.0, max(80.0, round(state["base_confidence"] + jitter, 1)))
    return jsonify(state)

@app.route("/api/simulate_force", methods=["POST"])
def simulate_force():
    global current_state_idx
    other_indices = [i for i in range(len(POSSIBLE_STATES)) if i != current_state_idx]
    current_state_idx = random.choice(other_indices)
    return jsonify({"status": "shifted", "new_state_idx": current_state_idx})
if __name__ == "__main__":
    print("=" * 60)
    print("[DASHBOARD SIMULATION ENGINE STARTED]")
    print("Running without ONNX models, OpenCV, or video upload requirement.")
    print("Dashboard available at: http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)