from __future__ import annotations

from typing import Any
import base64
import os

import cv2
import numpy as np
from flask import Flask, jsonify, request

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None

app = Flask(__name__)
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

model = None
if YOLO is not None:
    try:
        model = YOLO(MODEL_PATH)
    except Exception:
        model = None


def decode_frame(image_b64: str) -> np.ndarray:
    frame_bytes = base64.b64decode(image_b64)
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Invalid image payload")
    return frame


def detect_people(frame: np.ndarray) -> dict[str, Any]:
    if model is None:
        return {
            "occupancyCount": 0,
            "confidence": 0.0,
            "detections": [],
            "activity": "Class Finished",
        }

    results = model(frame, verbose=False)
    detections = []

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            if class_id != 0:
                continue
            xyxy = box.xyxy[0].tolist()
            detections.append(
                {
                    "label": "student",
                    "confidence": round(confidence, 3),
                    "bbox": {
                        "x1": round(float(xyxy[0]), 2),
                        "y1": round(float(xyxy[1]), 2),
                        "x2": round(float(xyxy[2]), 2),
                        "y2": round(float(xyxy[3]), 2),
                    },
                }
            )

    occupancy_count = len(detections)
    activity = "Class Running" if occupancy_count > 0 else "Class Finished"

    avg_confidence = (
        round(sum(item["confidence"] for item in detections) / occupancy_count, 3)
        if occupancy_count > 0
        else 0.0
    )

    return {
        "occupancyCount": occupancy_count,
        "confidence": avg_confidence,
        "detections": detections,
        "activity": activity,
    }


@app.get("/health")
def health() -> Any:
    return jsonify(
        {
            "status": "ok",
            "service": "smart-classroom-ai-model",
            "modelLoaded": model is not None,
        }
    )


@app.post("/infer")
def infer() -> Any:
    payload = request.get_json(silent=True) or {}
    image_b64 = payload.get("imageBase64")

    if not image_b64 or not isinstance(image_b64, str):
        return jsonify({"message": "imageBase64 is required"}), 400

    try:
        frame = decode_frame(image_b64)
        result = detect_people(frame)
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Inference pipeline failed")
        return jsonify({"message": "Inference failed"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
