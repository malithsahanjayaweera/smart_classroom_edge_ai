# SMART CLASSROOM EDGE AI SYSTEM

Production-ready university project demonstrating **Edge AI + Computer Vision + IoT-style automation** for smart classroom monitoring.

## Tech Stack

- **Frontend:** React + Vite + Tailwind CSS + TypeScript + Framer Motion + Recharts + React Router
- **Backend:** Node.js + Express
- **AI:** Python + YOLOv8 (Ultralytics) + OpenCV
- **Database:** MongoDB
- **Deployment:** Docker + Docker Compose

## Folder Structure

```text
smart_classroom_edge_ai/
├── frontend/                 # Premium monitoring dashboard
├── backend/                  # REST API + AC automation rules
├── ai-model/                 # YOLOv8/OpenCV inference service
├── docker/                   # Service Dockerfiles
├── docs/                     # API docs
├── dataset/                  # Dataset placeholder
├── simulation/               # Classroom simulator state assets
├── docker-compose.yml        # Multi-service local deployment
└── README.md
```

## Features

- Real-time occupancy monitoring (`LOW`, `MEDIUM`, `HIGH`)
- Classroom activity states:
  - Students Entering
  - Students Leaving
  - Janitor Cleaning
  - Class Running
  - Class Finished
- Automated AC control:
  - 0-2 students -> OFF
  - 3-9 students -> 24°C
  - 10+ students -> 20°C
- Live dashboard with glassmorphism dark blue UI
- Occupancy and temperature analytics charts
- Classroom simulation page

## Local Development

### 1) Backend

```bash
cd /home/runner/work/smart_classroom_edge_ai/smart_classroom_edge_ai/backend
npm install
npm run dev
```

Server: `http://localhost:5000`

### 2) Frontend

```bash
cd /home/runner/work/smart_classroom_edge_ai/smart_classroom_edge_ai/frontend
npm install
npm run dev
```

Dashboard: `http://localhost:5173`

### 3) AI Service (optional local run)

```bash
cd /home/runner/work/smart_classroom_edge_ai/smart_classroom_edge_ai/ai-model
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Service: `http://localhost:8000`

## API Summary

See `/docs/API.md`.

## Docker Deployment

```bash
cd /home/runner/work/smart_classroom_edge_ai/smart_classroom_edge_ai
docker compose up --build
```

Services:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:5000`
- AI model: `http://localhost:8000`
- MongoDB: `mongodb://localhost:27017`

## Sample Inference Update

```bash
curl -X POST http://localhost:5000/api/v1/inference \
  -H "Content-Type: application/json" \
  -d '{"occupancyCount":11,"activity":"Class Running","confidence":0.94,"detections":[]}'
```

