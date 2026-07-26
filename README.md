# 🎓 ClassSense AI

> **An Edge AI-Based Smart Classroom Occupancy Detection and Automated Climate Control System**

ClassSense AI is an Edge AI application that monitors classroom occupancy in real time using computer vision and automatically adjusts a simulated air-conditioning system based on the number of people detected. The system performs AI inference locally on an edge device, ensuring low latency, privacy, and offline operation.

This project was developed as part of the **Edge Computing** course at the **University of Jaffna**.

---

# 📖 Overview

Traditional classroom air-conditioning systems operate manually regardless of room occupancy, leading to unnecessary energy consumption.

ClassSense AI solves this problem by:

* Detecting classroom occupancy from a live camera feed
* Classifying occupancy into **LOW**, **MEDIUM**, or **HIGH**
* Automatically adjusting the AC state and temperature
* Displaying real-time information through a monitoring dashboard
* Running the AI model locally using Edge Computing

---

# 🚀 Features

* 👥 Real-time people detection
* 📊 Occupancy classification
* ❄️ Automatic AC control
* 📈 Live dashboard
* 📷 Camera or recorded video support
* ⚡ Edge AI inference
* 🐳 Docker deployment
* 📁 Modular project structure
* 🔄 MLOps-ready architecture

---

# 🏗️ System Architecture

```text
                 Camera
                    │
                    ▼
           Video Frame Capture
                    │
                    ▼
        AI Occupancy Detection Model
                    │
                    ▼
      LOW / MEDIUM / HIGH Occupancy
                    │
                    ▼
          AC Decision Controller
                    │
                    ▼
              Dashboard UI7
```

---


# 🛠 Technology Stack

## Programming

* Python 3.12+

## Computer Vision

* OpenCV
* YOLOv8 (or exported AI model)

## Backend

* FastAPI

## Dashboard

* Streamlit

## Containerization

* Docker

## Version Control

* Git & GitHub

---

# 📷 Dashboard

The dashboard displays:

* Live camera feed
* Number of detected people
* Occupancy level
* AC status
* Current temperature
* Last update timestamp
* Total AC running time
* Occupancy history

---

# 🔄 Workflow

```text
Capture Video
      │
      ▼
Detect People
      │
      ▼
Count Occupancy
      │
      ▼
Determine Occupancy Level
      │
      ▼
Control AC
      │
      ▼
Update Dashboard
```

---

# 📡 API Example

### GET

```text
/api/status
```

Example Response

```json
{
  "people": 7,
  "occupancy": "MEDIUM",
  "ac": "ON",
  "temperature": 24
}
```

---

# 📊 Example Dashboard

```text
--------------------------------------------

ClassSense AI Dashboard

People Detected : 7

Occupancy       : MEDIUM

AC Status       : ON

Temperature     : 24°C

Running Time    : 00:18:42

--------------------------------------------
```

---

# 🔒 Privacy

To protect participants' privacy:

* No face recognition
* No personal identification
* No participants under 15 years old
* Consent obtained before recording
* Local AI inference without cloud dependency

---

# 🎯 Future Improvements

* Real AC integration using IoT
* Mobile application
* Occupancy analytics
* MQTT communication
* Multi-camera support
* Energy usage reports
* Automatic attendance estimation

---

# 📚 Learning Outcomes

This project demonstrates practical knowledge in:

* Edge Computing
* Artificial Intelligence
* Computer Vision
* Docker
* FastAPI
* Streamlit
* Computer Networks
* GitHub Collaboration
* MLOps Fundamentals

---

# 📄 License

This project is developed for educational purposes as part of the **Edge Computing** course at the **University of Jaffna**.

---

# 👥 Contributors

Developed by the ClassSense AI Team

Department of Computer Science

University of Jaffna

Sri Lanka
