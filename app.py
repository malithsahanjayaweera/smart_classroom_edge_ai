import base64
import html
import os
import cv2
from flask import Flask, jsonify, render_template, request
import numpy as np
import onnxruntime as ort

app = Flask(__name__)


# Enable CORS for external frontends or local clients
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return response


# Load labels.txt if available
labels = []
if os.path.exists("labels.txt"):
    with open("labels.txt", "r") as f:
        labels = [html.unescape(line.strip()) for line in f.readlines()]

# Load ONNX model
MODEL_PATH = "model.onnx"
session = None
input_meta = None
output_meta = None

if os.path.exists(MODEL_PATH):
    session = ort.InferenceSession(MODEL_PATH)
    input_meta = session.get_inputs()[0]
    output_meta = session.get_outputs()

    print("=" * 60)
    print(f"[AZURE CV DEBUG] Loaded Model : {MODEL_PATH}")
    print(f"[AZURE CV DEBUG] Input Name   : {input_meta.name}")
    print(f"[AZURE CV DEBUG] Input Shape  : {input_meta.shape}")
    print(f"[AZURE CV DEBUG] Output Nodes : {[out.name for out in output_meta]}")
    print(f"[AZURE CV DEBUG] Labels       : {labels}")
    print("=" * 60)
else:
    print(f"[WARNING] Model file '{MODEL_PATH}' not found!")


def preprocess_frame_azure_cv(frame):
    """
    ONNX Model Preprocessing:
    1. BGR -> RGB
    2. Aspect-ratio preserving square center crop
    3. Raw float32 pixel values in [0..255] range (matching model training domain)
    4. NCHW tensor layout (1, 3, 224, 224)
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, _ = rgb.shape

    # Aspect ratio preserving center crop to square
    min_dim = min(h, w)
    top = (h - min_dim) // 2
    left = (w - min_dim) // 2
    crop = rgb[top:top+min_dim, left:left+min_dim]

    # Raw float32 pixel values in [0..255] range
    resized = cv2.resize(crop, (224, 224)).astype(np.float32)

    # NCHW Format (1, 3, 224, 224)
    img_trans = resized.transpose(2, 0, 1)
    return np.expand_dims(img_trans, axis=0)


def detect_human_presence(frame):
    """
    Analyzes frame for human skin tones, facial features, and color activity.
    Returns (is_human_detected, skin_percentage, texture_variance).
    """
    if frame is None or frame.size == 0:
        return False, 0.0, 0.0

    # 1. Human Skin Tone Detection (HSV space)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower1 = np.array([0, 20, 50], dtype=np.uint8)
    upper1 = np.array([25, 255, 255], dtype=np.uint8)
    lower2 = np.array([170, 20, 50], dtype=np.uint8)
    upper2 = np.array([180, 255, 255], dtype=np.uint8)

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    skin_mask = mask1 | mask2

    skin_pct = (np.sum(skin_mask > 0) / skin_mask.size) * 100.0

    # 2. Laplacian Variance (Texture / Detail / Activity)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Human presence criteria: requires skin/face tone signatures (>= 1.0%) or high dynamic variance (>= 200.0)
    is_present = (skin_pct >= 1.0) or (lap_var >= 200.0)
    return is_present, round(skin_pct, 2), round(lap_var, 2)


def parse_onnx_outputs(outputs):
    predicted_label = "UNKNOWN"
    confidence = 0.0

    top_label_str = None
    prob_dict = None

    for out in outputs:
        # ZipMap Dictionary Probabilities: [{'High(&gt;10)': 0.04, ...}]
        if isinstance(out, list) and len(out) > 0 and isinstance(out[0], dict):
            prob_dict = out[0]
        # String Label Array: [['Medium(3-9)']]
        elif isinstance(out, np.ndarray) and out.dtype.kind in ["U", "S", "O"]:
            top_label_str = str(out.flatten()[0])

    if prob_dict:
        top_key = max(prob_dict, key=prob_dict.get)
        predicted_label = html.unescape(top_key)
        confidence = float(prob_dict[top_key]) * 100.0
    elif top_label_str:
        predicted_label = html.unescape(top_label_str)
        confidence = 100.0

    return predicted_label, round(confidence, 1)


def get_occupancy_settings(predicted_label):
    lbl_clean = predicted_label.strip()
    lbl_upper = lbl_clean.upper()

    if "HIGH" in lbl_upper or ">10" in lbl_upper or "&GT;10" in lbl_upper or "10" in lbl_upper:
        return "HIGH (10 or higher)", "ON", "20°C", "#f87171"
    elif "LOW" in lbl_upper or "0-2" in lbl_upper or "0 - 2" in lbl_upper:
        return "LOW (0-2)", "OFF", "--", "#94a3b8"
    elif "SERVENT" in lbl_upper or "SERVANT" in lbl_upper:
        return "LOW (Servant)", "OFF", "--", "#94a3b8"
    elif "MEDIUM" in lbl_upper or "3-9" in lbl_upper or "3 - 9" in lbl_upper:
        return "MEDIUM (3-9)", "ON", "24°C", "#fbbf24"
    else:
        return lbl_clean if lbl_clean else "UNKNOWN", "OFF", "--", "#94a3b8"




@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": session is not None})


@app.route("/predict_frame", methods=["POST"])
def predict_frame():
    try:
        if session is None:
            return jsonify({"error": "Model not loaded"}), 500

        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image data"}), 400

        image_data = data["image"].split(",")[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid frame decode"}), 400

        # 1. Human Presence Verification Check
        is_human_present, skin_pct, lap_var = detect_human_presence(frame)

        if not is_human_present:
            print(f"[INFERENCE] No humans detected (Skin: {skin_pct}%, Variance: {lap_var}) -> Outputting LOW (0-2)")
            return jsonify({
                "occupancy": "LOW (0-2)",
                "ac_state": "OFF",
                "temp": "--",
                "color": "#94a3b8",
                "confidence": 99.0,
                "predicted_label": "No Humans Detected",
                "human_detected": False
            })

        # 2. Preprocess with Azure Custom Vision standards (0-1 normalized)
        input_data = preprocess_frame_azure_cv(frame)

        # 3. Model Inference
        outputs = session.run(None, {input_meta.name: input_data})

        # 4. Parse output label and confidence
        predicted_label, confidence = parse_onnx_outputs(outputs)

        print(f"[INFERENCE] Label: '{predicted_label}' | Confidence: {confidence}% | Skin: {skin_pct}%")

        # 5. Map to occupancy & AC settings
        occupancy, ac_state, temp, color = get_occupancy_settings(predicted_label)

        return jsonify({
            "occupancy": occupancy,
            "ac_state": ac_state,
            "temp": temp,
            "color": color,
            "confidence": confidence,
            "predicted_label": predicted_label,
            "human_detected": True
        })

    except Exception as e:
        print(f"[ERROR in predict_frame]: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)