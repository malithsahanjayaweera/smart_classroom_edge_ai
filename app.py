import base64
import os
import cv2
from flask import Flask, jsonify, render_template_string, request
import numpy as np
import onnxruntime as ort

app = Flask(__name__)

# labels.txt load කිරීම
labels = []
if os.path.exists("labels.txt"):
    with open("labels.txt", "r") as f:
        labels = [line.strip() for line in f.readlines()]

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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Classroom Edge AI System</title>
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #f8fafc; color: #1e293b; margin: 0; padding: 30px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { margin-bottom: 25px; }
        .header h3 { color: #0284c7; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; margin: 0 0 5px 0; }
        .header h1 { color: #0f172a; font-size: 28px; font-weight: 700; margin: 0; }
        
        .dashboard-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 25px; align-items: start; }
        
        .monitoring-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e2e8f0; }
        .video-box { background: #000; border-radius: 12px; width: 100%; height: 320px; margin: 15px auto; overflow: hidden; display: flex; justify-content: center; align-items: center; position: relative; }
        video { width: 100%; height: 100%; object-fit: contain; }
        .placeholder-icon svg { width: 80px; height: 80px; fill: #0284c7; }
        
        .upload-form { margin-top: 15px; text-align: center; }
        .file-input { display: none; }
        .file-label { background: #0284c7; color: white; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; display: inline-block; transition: 0.2s; }
        .file-label:hover { background: #0369a1; }

        .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; border-left: 6px solid #0284c7; box-shadow: 0 2px 4px rgba(0,0,0,0.04); border-top: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
        .card-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 5px; }
        .card-sub { font-size: 12px; color: #64748b; }
        .card-value { font-size: 22px; font-weight: 800; color: #0284c7; margin-top: 8px; }

        .extra-credits { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 20px; }
        .extra-title { color: #0369a1; font-weight: 700; font-size: 13px; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 10px; }
        .extra-credits p { margin: 5px 0; font-size: 14px; color: #334155; }
        .extra-credits ul { margin: 5px 0 0 20px; padding: 0; font-size: 13px; color: #475569; }
        
        .footer-text { margin-top: 30px; font-size: 12px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h3>DASHBOARD</h3>
            <h1>Make the system state visible during the demo</h1>
        </div>

        <div class="dashboard-grid">
            <div class="monitoring-card">
                <div class="video-box" id="videoContainer">
                    <div class="placeholder-icon" id="placeholder">
                        <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 10h2v7H7zm4-3h2v10h-2zm4 6h2v4h-2z"/></svg>
                    </div>
                    <video id="videoPlayer" controls style="display:none;"></video>
                </div>
                <p style="color: #64748b; font-size: 13px;">A monitoring view that shows what the system is doing, live, while it runs.</p>
                
                <div class="upload-form">
                    <label for="video-upload" class="file-label">Select Video for Live Demo</label>
                    <input id="video-upload" class="file-input" type="file" accept="video/*">
                </div>
            </div>

            <div>
                <div class="cards-grid">
                    <div class="card">
                        <div class="card-title">Occupancy level</div>
                        <div class="card-sub">Real-time LOW / MEDIUM / HIGH</div>
                        <div class="card-value" id="val-occupancy">--</div>
                    </div>

                    <div class="card">
                        <div class="card-title">AC state</div>
                        <div class="card-sub">ON or OFF</div>
                        <div class="card-value" id="val-ac-state">--</div>
                    </div>

                    <div class="card">
                        <div class="card-title">Temperature</div>
                        <div class="card-sub">Current setting in °C</div>
                        <div class="card-value" id="val-temp">--</div>
                    </div>

                    <div class="card">
                        <div class="card-title">AC running time</div>
                        <div class="card-sub">Total time the AC has run</div>
                        <div class="card-value" id="val-ac-time">0.0s</div>
                    </div>
                </div>

                <div class="extra-credits">
                    <div class="extra-title">OPTIONAL — EXTRA CREDITS</div>
                    <p><strong>Configured Thresholds:</strong></p>
                    <ul>
                        <li><strong>0 - 2 People (LOW):</strong> AC OFF</li>
                        <li><strong>3 - 9 People (MEDIUM):</strong> AC ON (24°C)</li>
                        <li><strong>> 9 People (HIGH):</strong> AC ON (20°C)</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer-text">
            <span>Smart Classroom Edge AI System</span>
        </div>
    </div>

    <script>
        const video = document.getElementById('videoPlayer');
        const placeholder = document.getElementById('placeholder');
        const uploadInput = document.getElementById('video-upload');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        let acRunningTimeSeconds = 0;
        let processInterval = null;

        uploadInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const videoURL = URL.createObjectURL(file);
                video.src = videoURL;
                placeholder.style.display = 'none';
                video.style.display = 'block';
                
                acRunningTimeSeconds = 0;
                document.getElementById('val-ac-time').innerText = '0.0s';
                
                video.play();
                startLoop();
            }
        });

        function startLoop() {
            if (processInterval) clearInterval(processInterval);

            processInterval = setInterval(() => {
                if (video.paused || video.ended) return;

                const w = 224;
                const h = 224;
                canvas.width = w;
                canvas.height = h;

                try {
                    ctx.drawImage(video, 0, 0, w, h);
                    const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);

                    fetch('/predict_frame', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: imageBase64 })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) return;

                        document.getElementById('val-occupancy').innerText = data.occupancy;
                        
                        const acEl = document.getElementById('val-ac-state');
                        acEl.innerText = data.ac_state;
                        acEl.style.color = data.ac_state === 'ON' ? '#16a34a' : '#dc2626';

                        document.getElementById('val-temp').innerText = data.temp;

                        if (data.ac_state === 'ON') {
                            acRunningTimeSeconds += 0.5;
                        }
                        document.getElementById('val-ac-time').innerText = acRunningTimeSeconds.toFixed(1) + 's';
                    })
                    .catch(err => console.error(err));

                } catch (e) {
                    console.error("Canvas draw error:", e);
                }

            }, 500);
        }
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE)


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
        h, w = 224, 224
        if len(input_meta.shape) == 4:
            if input_meta.shape[1] == 3:
                h, w = input_meta.shape[2], input_meta.shape[3]
            elif input_meta.shape[3] == 3:
                h, w = input_meta.shape[1], input_meta.shape[2]

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(frame_rgb, (w, h))
        img_float = resized.astype(np.float32)

        if len(input_meta.shape) == 4 and input_meta.shape[1] == 3:
            img_float = img_float.transpose(2, 0, 1)

        input_data = np.expand_dims(img_float, axis=0)

        # Model Inference
        outputs = session.run(None, {input_meta.name: input_data})

        predicted_label = "UNKNOWN"

        # Azure Custom Vision Output Parser
        for out in outputs:
            # 1. ZipMap (Dictionary Probability)
            if (
                isinstance(out, list)
                and len(out) > 0
                and isinstance(out[0], dict)
            ):
                prob_dict = out[0]
                predicted_label = max(prob_dict, key=prob_dict.get)
                print(
                    f"[AZURE CV DICT] Top: '{predicted_label}' | Probabilities: {prob_dict}"
                )
                break
            # 2. String Label Array
            elif isinstance(out, np.ndarray) and out.dtype.kind in [
                "U",
                "S",
                "O",
            ]:
                predicted_label = str(out.flatten()[0])
                print(f"[AZURE CV STRING] Predicted: '{predicted_label}'")
                break
            elif isinstance(out, (list, tuple)) and isinstance(out[0], str):
                predicted_label = str(out[0])
                print(f"[AZURE CV LIST STRING] Predicted: '{predicted_label}'")
                break
            # 3. Numeric Tensor Logits
            elif isinstance(out, np.ndarray) and np.issubdtype(
                out.dtype, np.number
            ):
                flat = out.flatten()
                top_idx = int(np.argmax(flat))
                if labels and top_idx < len(labels):
                    predicted_label = labels[top_idx]
                else:
                    predicted_label = f"CLASS_{top_idx}"
                print(
                    f"[AZURE CV NUMERIC] Top Index: {top_idx} ('{predicted_label}') | Scores: {flat}"
                )
                break

        lbl_upper = predicted_label.upper()

        # Dashboard Logic Matching
        if "HIGH" in lbl_upper or ">10" in lbl_upper:
            occupancy = "HIGH (>10)"
            ac_state = "ON"
            temp = "20°C"
        elif "LOW" in lbl_upper or "0-2" in lbl_upper:
            occupancy = "LOW (0-2)"
            ac_state = "OFF"
            temp = "--"
        elif "SERVENT" in lbl_upper or "SERVANT" in lbl_upper:
            occupancy = "LOW (Servent)"
            ac_state = "OFF"
            temp = "--"
        elif "MEDIUM" in lbl_upper or "3-9" in lbl_upper:
            occupancy = "MEDIUM (3-9)"
            ac_state = "ON"
            temp = "24°C"
        else:
            occupancy = predicted_label
            ac_state = "ON"
            temp = "24°C"

        return jsonify(
            {"occupancy": occupancy, "ac_state": ac_state, "temp": temp}
        )

    except Exception as e:
        print(f"[ERROR]: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)