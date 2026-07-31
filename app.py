import base64
import html
import os
import cv2
from flask import Flask, jsonify, render_template_string, request
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
    print(
        f"[AZURE CV DEBUG] Output Nodes : {[out.name for out in output_meta]}"
    )
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


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Classroom Edge AI System</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif; }
        body { 
            background: #0b0f19; 
            color: #f8fafc; 
            margin: 0; 
            padding: 30px; 
            min-height: 100vh;
            background-image: 
                radial-gradient(at 20% 20%, rgba(56, 189, 248, 0.08) 0px, transparent 50%),
                radial-gradient(at 80% 80%, rgba(99, 102, 241, 0.08) 0px, transparent 50%);
        }
        .container { max-width: 1320px; margin: 0 auto; }
        
        .top-bar { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08); 
        }
        .header h3 { 
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-transform: uppercase; 
            font-size: 12px; 
            letter-spacing: 2px; 
            margin: 0 0 6px 0; 
            font-weight: 800; 
        }
        .header h1 { color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
        
        .status-badge { 
            display: inline-flex; 
            align-items: center; 
            gap: 10px; 
            background: rgba(30, 41, 59, 0.7); 
            backdrop-filter: blur(12px);
            padding: 10px 20px; 
            border-radius: 9999px; 
            font-size: 13px; 
            font-weight: 600; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #f87171; }
        .status-dot.connected { background: #4ade80; box-shadow: 0 0 12px #4ade80; }
        
        .dashboard-grid { display: grid; grid-template-columns: 1.25fr 1fr; gap: 30px; align-items: start; }
        
        .monitoring-card { 
            background: rgba(17, 24, 39, 0.7); 
            backdrop-filter: blur(16px);
            border-radius: 20px; 
            padding: 24px; 
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
        }
        .video-box { 
            background: #030712; 
            border-radius: 16px; 
            width: 100%; 
            height: 380px; 
            margin: 0 0 20px 0; 
            overflow: hidden; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            position: relative; 
            border: 1px solid rgba(255, 255, 255, 0.08); 
        }
        video { width: 100%; height: 100%; object-fit: contain; }
        
        .placeholder-icon { display: flex; flex-direction: column; align-items: center; gap: 14px; color: #64748b; text-align: center; }
        .placeholder-icon svg { width: 56px; height: 56px; fill: #38bdf8; opacity: 0.9; filter: drop-shadow(0 0 12px rgba(56, 189, 248, 0.3)); }
        .placeholder-icon span { font-size: 14px; font-weight: 500; }
        
        .controls-row { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
        .btn { 
            background: linear-gradient(135deg, #0284c7, #2563eb); 
            color: white; 
            padding: 12px 24px; 
            border-radius: 12px; 
            border: none; 
            cursor: pointer; 
            font-weight: 600; 
            font-size: 14px; 
            display: inline-flex; 
            align-items: center; 
            gap: 10px; 
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); 
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4); }
        .btn-secondary { 
            background: rgba(30, 41, 59, 0.8); 
            color: #f8fafc; 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            box-shadow: none;
        }
        .btn-secondary:hover { background: rgba(51, 65, 85, 0.9); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .file-input { display: none; }

        .cards-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { 
            background: rgba(17, 24, 39, 0.7); 
            backdrop-filter: blur(16px);
            padding: 24px; 
            border-radius: 20px; 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); 
            transition: all 0.25s ease; 
        }
        .card:hover { border-color: rgba(56, 189, 248, 0.4); transform: translateY(-2px); }
        .card-title { font-size: 12px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .card-value { font-size: 28px; font-weight: 800; color: #ffffff; margin-top: 4px; display: flex; align-items: center; gap: 10px; }
        .card-sub { font-size: 13px; color: #64748b; margin-top: 8px; font-weight: 500; }
        
        .confidence-bar-bg { width: 100%; height: 6px; background: rgba(51, 65, 85, 0.5); border-radius: 999px; margin-top: 12px; overflow: hidden; }
        .confidence-bar-fill { height: 100%; width: 0%; background: linear-gradient(90deg, #38bdf8, #818cf8); transition: width 0.4s ease; }

        .footer-text { margin-top: 40px; font-size: 13px; color: #475569; text-align: center; font-weight: 500; }
        
        .ac-pulse { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .ac-pulse.on { background: #4ade80; box-shadow: 0 0 14px #4ade80; animation: pulse 1.5s infinite; }
        .ac-pulse.off { background: #f87171; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <div class="header">
                <h3>SMART CLASSROOM EDGE AI</h3>
                <h1>Live Edge Computer Vision Dashboard</h1>
            </div>
            <div class="status-badge">
                <span class="status-dot" id="backend-status-dot"></span>
                <span id="backend-status-text">Connecting to Edge API...</span>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="monitoring-card">
                <div class="video-box" id="videoContainer">
                    <div class="placeholder-icon" id="placeholder">
                        <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zM7 10h2v7H7zm4-3h2v10h-2zm4 6h2v4h-2z"/></svg>
                        <span>Select a Demo Video or Start Live Camera</span>
                    </div>
                    <video id="videoPlayer" controls playsinline style="display:none;"></video>
                </div>
                <p style="color: #64748b; font-size: 13px; margin: 0 0 20px 0; text-align: center; font-weight: 500;">
                    Live frame capture stream to Azure CV ONNX inference engine (224x224 normalized).
                </p>
                
                <div class="controls-row">
                    <label for="video-upload" class="btn">
                        📁 Select Demo Video
                    </label>
                    <input id="video-upload" class="file-input" type="file" accept="video/*">
                    
                    <button class="btn btn-secondary" id="btn-webcam" onclick="toggleWebcam()">
                        📷 Start Camera
                    </button>
                </div>
            </div>

            <div>
                <div class="cards-grid">
                    <div class="card">
                        <div class="card-title">Occupancy Level</div>
                        <div class="card-value" id="val-occupancy" style="color: #38bdf8;">--</div>
                        <div class="card-sub" id="lbl-confidence">Confidence: --%</div>
                        <div class="confidence-bar-bg">
                            <div class="confidence-bar-fill" id="val-conf-bar"></div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-title">AC State</div>
                        <div class="card-value" id="val-ac-state">
                            <span class="ac-pulse off" id="ac-pulse"></span>
                            <span id="txt-ac-state">--</span>
                        </div>
                        <div class="card-sub">Automatic Relay Signal</div>
                    </div>

                    <div class="card">
                        <div class="card-title">Target Temperature</div>
                        <div class="card-value" id="val-temp" style="color: #38bdf8;">--</div>
                        <div class="card-sub">Current Setpoint in °C</div>
                    </div>

                    <div class="card">
                        <div class="card-title">AC Running Time</div>
                        <div class="card-value" id="val-ac-time" style="color: #38bdf8;">0.0s</div>
                        <div class="card-sub">Total Active Time</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer-text">
            <span>Smart Classroom Edge AI System &bull; ONNX Model Engine &bull; Real-Time Inference</span>
        </div>
    </div>

    <script>
        const video = document.getElementById('videoPlayer');
        const placeholder = document.getElementById('placeholder');
        const uploadInput = document.getElementById('video-upload');
        const btnWebcam = document.getElementById('btn-webcam');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        let acRunningTimeSeconds = 0;
        let processInterval = null;
        let webcamStream = null;
        let isWebcamActive = false;

        // Backend Health Check
        function checkBackendHealth() {
            fetch('/health')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        document.getElementById('backend-status-dot').className = 'status-dot connected';
                        document.getElementById('backend-status-text').innerText = 'Edge AI API Connected';
                    }
                })
                .catch(err => {
                    document.getElementById('backend-status-dot').className = 'status-dot';
                    document.getElementById('backend-status-text').innerText = 'API Disconnected';
                });
        }
        checkBackendHealth();
        setInterval(checkBackendHealth, 5000);

        // Video File Upload
        uploadInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                stopWebcam();
                const videoURL = URL.createObjectURL(file);
                video.srcObject = null;
                video.src = videoURL;
                video.muted = true; // Prevents browser autoplay blocking
                placeholder.style.display = 'none';
                video.style.display = 'block';
                
                acRunningTimeSeconds = 0;
                document.getElementById('val-ac-time').innerText = '0.0s';
                
                video.play().then(() => startLoop()).catch(err => console.error("Play error:", err));
            }
        });

        // Toggle Live Webcam
        function toggleWebcam() {
            if (isWebcamActive) {
                stopWebcam();
            } else {
                startWebcam();
            }
        }

        function startWebcam() {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
                    .then(stream => {
                        webcamStream = stream;
                        isWebcamActive = true;
                        video.src = '';
                        video.srcObject = stream;
                        video.muted = true;
                        placeholder.style.display = 'none';
                        video.style.display = 'block';
                        btnWebcam.innerText = '⏹️ Stop Camera';
                        btnWebcam.classList.add('btn-secondary');
                        
                        acRunningTimeSeconds = 0;
                        document.getElementById('val-ac-time').innerText = '0.0s';
                        
                        video.play().then(() => startLoop()).catch(err => console.error("Webcam play error:", err));
                    })
                    .catch(err => {
                        alert("Could not access webcam: " + err.message);
                    });
            }
        }

        function stopWebcam() {
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
                webcamStream = null;
            }
            isWebcamActive = false;
            btnWebcam.innerText = '📷 Start Camera';
            if (processInterval) clearInterval(processInterval);
        }

        video.addEventListener('play', () => startLoop());
        video.addEventListener('pause', () => stopLoop());
        video.addEventListener('ended', () => stopLoop());

        function stopLoop() {
            if (processInterval) {
                clearInterval(processInterval);
                processInterval = null;
            }
        }

        function startLoop() {
            if (processInterval) clearInterval(processInterval);

            processInterval = setInterval(() => {
                if (video.paused || video.ended || video.readyState < 2) return;

                const videoW = video.videoWidth || 640;
                const videoH = video.videoHeight || 480;
                canvas.width = videoW;
                canvas.height = videoH;

                try {
                    ctx.drawImage(video, 0, 0, videoW, videoH);
                    const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);

                    fetch('/predict_frame', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: imageBase64 })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) {
                            console.error("Prediction error:", data.error);
                            return;
                        }

                        // Update Occupancy
                        const occEl = document.getElementById('val-occupancy');
                        occEl.innerText = data.occupancy;
                        if (data.color) occEl.style.color = data.color;

                        // Update Confidence
                        document.getElementById('lbl-confidence').innerText = 'Confidence: ' + (data.confidence || 0) + '%';
                        document.getElementById('val-conf-bar').style.width = (data.confidence || 0) + '%';

                        // Update AC State
                        const txtAc = document.getElementById('txt-ac-state');
                        const pulseAc = document.getElementById('ac-pulse');
                        txtAc.innerText = data.ac_state;
                        
                        if (data.ac_state === 'ON') {
                            txtAc.style.color = '#4ade80';
                            pulseAc.className = 'ac-pulse on';
                            acRunningTimeSeconds += 0.5;
                        } else {
                            txtAc.style.color = '#f87171';
                            pulseAc.className = 'ac-pulse off';
                        }

                        // Update Temperature & Running Time
                        document.getElementById('val-temp').innerText = data.temp;
                        document.getElementById('val-ac-time').innerText = acRunningTimeSeconds.toFixed(1) + 's';
                    })
                    .catch(err => console.error("Fetch error:", err));

                } catch (e) {
                    console.error("Canvas capture error:", e);
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

        # Save frame sample for debugging
        cv2.imwrite("debug_frame.jpg", frame)

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