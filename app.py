import base64
from collections import Counter, deque
import html
import json
import os
import cv2
from flask import Flask, jsonify, render_template, request
import numpy as np
import onnxruntime as ort

app = Flask(__name__)

# Output Smoothing & Transition Mechanism Buffers
PROB_BUFFER_SIZE = 5
TARGET_BUFFER_SIZE = 3
prob_history = deque(maxlen=PROB_BUFFER_SIZE)
target_history = deque(maxlen=TARGET_BUFFER_SIZE)
current_state_idx = None

# labels.txt load කිරීම
# Custom Vision labels HTML-escaped ලෙස export වෙනවා ("High(&gt;10)"), ඒ නිසා unescape කරනවා
labels = []
if os.path.exists("labels.txt"):
    with open("labels.txt", "r", encoding="utf-8") as f:
        labels = [html.unescape(line.strip()) for line in f if line.strip()]

# ONNX model load කිරීම
session = ort.InferenceSession("model.onnx")

# Diagnostic Model Info Print
input_meta = session.get_inputs()[0]
output_meta = session.get_outputs()

print("=" * 60)
print(f"[AZURE CV DEBUG] Input Name  : {input_meta.name}")
print(f"[AZURE CV DEBUG] Input Shape : {input_meta.shape}")
print(
    f"[AZURE CV DEBUG] Output Nodes: {[out.name for out in output_meta]}"
)
print("=" * 60)


def _describe_model():
    """Landing page එකේ පෙන්නන්න, load වුණු model එකේ ඇත්ත specs ටික ගන්නවා."""
    shape = input_meta.shape
    if len(shape) == 4 and shape[1] == 3:
        resolution = f"{shape[2]} × {shape[3]} × 3"
    elif len(shape) == 4:
        resolution = f"{shape[1]} × {shape[2]} × {shape[3]}"
    else:
        resolution = " × ".join(str(d) for d in shape)

    try:
        size_mb = os.path.getsize("model.onnx") / (1024 * 1024)
    except OSError:
        size_mb = 0.0

    return {
        "resolution": resolution,
        "classes": len(labels),
        "size_mb": f"{size_mb:.1f}",
        "runtime": ort.__version__,
        "labels": labels,
    }


MODEL_INFO = _describe_model()


def _preproc_spec():
    """metadata_properties.json එකේ තියෙන resize/crop spec එක කියවනවා."""
    crop_h = crop_w = 224
    if len(input_meta.shape) == 4:
        try:
            if input_meta.shape[1] == 3:
                crop_h, crop_w = int(input_meta.shape[2]), int(input_meta.shape[3])
            elif input_meta.shape[3] == 3:
                crop_h, crop_w = int(input_meta.shape[1]), int(input_meta.shape[2])
        except (TypeError, ValueError):
            pass

    target_h, target_w = 256, 256
    try:
        with open("metadata_properties.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
        crop_h = int(meta.get("CustomVision.Preprocess.CropHeight") or crop_h)
        crop_w = int(meta.get("CustomVision.Preprocess.CropWidth") or crop_w)
        target_h = int(meta.get("CustomVision.Preprocess.TargetHeight") or target_h)
        target_w = int(meta.get("CustomVision.Preprocess.TargetWidth") or target_w)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

    return crop_h, crop_w, target_h, target_w


CROP_H, CROP_W, TARGET_H, TARGET_W = _preproc_spec()
print(
    f"[PREPROCESS] ByShorterSide -> {TARGET_H} px, "
    f"centre crop -> {CROP_H}x{CROP_W}, pixel range 0-255"
)
print("=" * 60)


def preprocess(rgb):
    """ResizeMethod=ByShorterSide + CropMethod=OneCropCenter.

    කලින් තිබුණේ කෙළින්ම 224x224 ට resize කිරීමක් -- ඒකෙන් 16:9 frame එක
    හතරැස් කරලා විකෘති වෙනවා, model එකට වැරදි උත්තර දෙන්න හේතු වෙනවා.

    NOTE: metadata එකේ NominalPixelRange "Normalized_0_1" කියලා තිබුණත්,
    හිස් classroom footage එකට එරෙහිව මැන බැලුවම නිවැරදි answer එක දෙන්නේ
    0-255 range එකයි (0-1 දුන්නම වැරදියට Medium කියනවා). ඒ නිසා pixels
    scale කරන්නේ නැහැ.
    """
    h, w = rgb.shape[:2]
    if h == 0 or w == 0:
        raise ValueError("empty frame")

    # ByShorterSide: කෙටි පැත්ත target එකට ගේනවා, aspect ratio එක රැකගෙන
    scale = max(TARGET_H / h, TARGET_W / w)
    new_w = max(CROP_W, int(round(w * scale)))
    new_h = max(CROP_H, int(round(h * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(rgb, (new_w, new_h), interpolation=interp)

    # OneCropCenter
    y = (new_h - CROP_H) // 2
    x = (new_w - CROP_W) // 2
    cropped = resized[y:y + CROP_H, x:x + CROP_W]

    return cropped.astype(np.float32)


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html", active="home", model=MODEL_INFO)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("dashboard.html", active="dashboard")


@app.route("/predict_frame", methods=["POST"])
def predict_frame():
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image data"}), 400

        image_data = data["image"].split(",")[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"error": "Invalid frame decode"}), 400

        # Frame එක පරික්ෂාවට image file එකක් ලෙස save කරගැනීම
        cv2.imwrite("debug_frame.jpg", frame)

        # Preprocessing Azure Custom Vision
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_float = preprocess(frame_rgb)

        if len(input_meta.shape) == 4 and input_meta.shape[1] == 3:
            img_float = img_float.transpose(2, 0, 1)

        input_data = np.expand_dims(img_float, axis=0)

        # Model Inference
        outputs = session.run(None, {input_meta.name: input_data})

        predicted_label = ""
        prob_dict = {}

        # Azure Custom Vision Output Parser
        # මේ model එකේ outputs දෙකක් තියෙනවා: 'classLabel' (string) සහ 'loss' (ZipMap).
        # දෙකම කියවනවා -- classLabel එකෙන් label එකත්, loss එකෙන් probabilities ත්.
        for out in outputs:
            # 1. ZipMap (Dictionary Probability)
            if (
                isinstance(out, list)
                and len(out) > 0
                and isinstance(out[0], dict)
            ):
                prob_dict = {
                    html.unescape(str(k)): float(v)
                    for k, v in out[0].items()
                }
            # 2. String Label Array
            elif isinstance(out, np.ndarray) and out.dtype.kind in [
                "U",
                "S",
                "O",
            ]:
                predicted_label = html.unescape(str(out.flatten()[0]))
            elif isinstance(out, (list, tuple)) and isinstance(out[0], str):
                predicted_label = html.unescape(str(out[0]))
            # 3. Numeric Tensor Logits
            elif isinstance(out, np.ndarray) and np.issubdtype(
                out.dtype, np.number
            ):
                flat = out.flatten()
                if labels and len(flat) == len(labels):
                    prob_dict = {
                        labels[i]: float(flat[i]) for i in range(len(flat))
                    }
                else:
                    top_idx = int(np.argmax(flat))
                    predicted_label = (
                        labels[top_idx]
                        if labels and top_idx < len(labels)
                        else f"CLASS_{top_idx}"
                    )

        # classLabel එකක් නැත්නම් probabilities වලින් top එක ගන්නවා
        if not predicted_label and prob_dict:
            predicted_label = max(prob_dict, key=prob_dict.get)
        if not predicted_label:
            predicted_label = "UNKNOWN"

        # Moving Average of probabilities to stabilize output transitions
        if prob_dict:
            prob_history.append(prob_dict)
            smoothed_prob_dict = {}
            all_keys = set().union(*(p.keys() for p in prob_history))
            for k in all_keys:
                smoothed_prob_dict[k] = sum(p.get(k, 0.0) for p in prob_history) / len(prob_history)
            prob_dict = smoothed_prob_dict
            predicted_label = max(prob_dict, key=prob_dict.get)

        confidence = float(prob_dict.get(predicted_label, 0.0))

        # Distribution එක labels.txt පිළිවෙළට තියාගන්නවා -- bars එහෙම නටන්නේ නැති වෙන්න
        order = labels if labels else sorted(prob_dict)
        distribution = [
            {"label": name, "value": float(prob_dict.get(name, 0.0))}
            for name in order
            if name in prob_dict
        ]
        for name, value in prob_dict.items():
            if name not in order:
                distribution.append({"label": name, "value": float(value)})

        print(
            f"[AZURE CV] Predicted: '{predicted_label}' "
            f"({confidence * 100:.1f}%) | {prob_dict}"
        )

        lbl_upper = predicted_label.upper()

        # Target state index mapping (0: LOW, 1: MEDIUM, 2: HIGH, 3: SERVANT)
        if "SERVENT" in lbl_upper or "SERVANT" in lbl_upper:
            raw_target_idx = 3
        elif "HIGH" in lbl_upper or ">10" in lbl_upper:
            raw_target_idx = 2
        elif "LOW" in lbl_upper or "0-2" in lbl_upper:
            raw_target_idx = 0
        elif "MEDIUM" in lbl_upper or "3-9" in lbl_upper:
            raw_target_idx = 1
        else:
            raw_target_idx = 1

        # Debouncing target index over recent frames to filter noise
        target_history.append(raw_target_idx)
        debounced_target_idx = Counter(target_history).most_common(1)[0][0]

        # Smooth Step-by-Step State Transition Mechanism
        global current_state_idx
        if current_state_idx is None:
            current_state_idx = debounced_target_idx
        else:
            if current_state_idx != debounced_target_idx:
                if debounced_target_idx == 3:
                    current_state_idx = 3
                elif current_state_idx == 3:
                    current_state_idx = 0
                else:
                    if debounced_target_idx > current_state_idx:
                        current_state_idx += 1
                    else:
                        current_state_idx -= 1

        # Dashboard Logic Matching based on smoothed step-by-step state
        override = False

        if current_state_idx == 3:
            occupancy = "LOW (Servent)"
            ac_state = "OFF"
            temp = "--"
            override = True
            reason = "Servant detected — AC forced OFF"
        elif current_state_idx == 2:
            occupancy = "HIGH (>10)"
            ac_state = "ON"
            temp = "20°C"
            reason = "Occupancy band HIGH (>10)"
        elif current_state_idx == 0:
            occupancy = "LOW (0-2)"
            ac_state = "OFF"
            temp = "--"
            reason = "Occupancy band LOW (0-2)"
        elif current_state_idx == 1:
            occupancy = "MEDIUM (3-9)"
            ac_state = "ON"
            temp = "24°C"
            reason = "Occupancy band MEDIUM (3-9)"
        else:
            occupancy = predicted_label
            ac_state = "ON"
            temp = "24°C"
            reason = f"Unmapped tag '{predicted_label}' — default policy"

        return jsonify(
            {
                "occupancy": occupancy,
                "ac_state": ac_state,
                "temp": temp,
                "label": predicted_label,
                "confidence": confidence,
                "distribution": distribution,
                "override": override,
                "reason": reason,
            }
        )

    except Exception as e:
        print(f"[ERROR]: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
