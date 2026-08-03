import cv2
import numpy as np
import onnxruntime as ort
from collections import deque, Counter

input_video_path = "IMG_8798.MOV"
output_video_path = "output_video.mp4"

# 1. Load ONNX Model
session = ort.InferenceSession("model.onnx")
input_name = session.get_inputs()[0].name

# 2. Open Video
cap = cv2.VideoCapture(input_video_path)

if not cap.isOpened():
    print(f"❌ Error: Video file '{input_video_path}' open කරගන්න බැරි වුනා.")
    exit()

# Video Metadata
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps    = cap.get(cv2.CAP_PROP_FPS)
if fps == 0 or np.isnan(fps):
    fps = 30.0

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

def preprocess_frame_center_crop(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Aspect Ratio Preserving Center Crop
    h, w, _ = img.shape
    min_dim = min(h, w)
    top = (h - min_dim) // 2
    left = (w - min_dim) // 2
    crop_img = img[top:top+min_dim, left:left+min_dim]
    
    resized = cv2.resize(crop_img, (224, 224)).astype(np.float32)
    img_data = np.transpose(resized, (2, 0, 1))
    img_data = np.expand_dims(img_data, axis=0)
    return img_data

# Buffer for Temporal Smoothing (Stores last 30 frames predictions)
BUFFER_SIZE = 30 
prediction_history = deque(maxlen=BUFFER_SIZE)

print("🚀 Smart AC Control System (Smooth Tracking Enabled)...")
print("💡 Press 'q' on video window to stop.\n")

frame_count = 0

try:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        input_data = preprocess_frame_center_crop(frame)

        # Run ONNX Inference
        outputs = session.run(None, {input_name: input_data})

        # Extract Raw Instant Label
        raw_output = outputs[0][0]
        if isinstance(raw_output, (list, np.ndarray)):
            raw_label = str(raw_output[0])
        else:
            raw_label = str(raw_output)

        raw_label = raw_label.strip("[]'\"")
        
        # Add to Buffer for Smoothing
        prediction_history.append(raw_label)

        # Get Most Frequent Label in the last 30 frames (Stable Prediction)
        stable_label = Counter(prediction_history).most_common(1)[0][0]

        # Extract Confidence Scores
        confidence = 0.0
        if len(outputs) > 1:
            probs = outputs[1][0]
            if isinstance(probs, dict):
                confidence = probs.get(raw_label, 0.0) * 100

        # ========================================================
        # 🧠 SMOOTHED SMART AC CONTROL LOGIC
        # ========================================================
        label_lower = stable_label.lower()

        if "low" in label_lower:
            ac_status = "OFF"
            ac_temp = "N/A"
            status_color = (0, 0, 255)      # Red for OFF
        elif "medium" in label_lower:
            ac_status = "ON"
            ac_temp = "24°C"
            status_color = (0, 255, 255)    # Yellow for Normal
        elif "high" in label_lower:
            ac_status = "ON"
            ac_temp = "20°C"
            status_color = (0, 255, 0)      # Green for Maximum Cooling
        else:
            ac_status = "OFF"
            ac_temp = "N/A"
            status_color = (200, 200, 200)

        # UI Overlay Box
        cv2.rectangle(frame, (20, 15), (580, 130), (0, 0, 0), -1)

        # Display Instant & Stable Labels
        text_level = f"Raw: {raw_label[:10]}.. | Stable: {stable_label}"
        cv2.putText(frame, text_level, (30, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Display AC Status
        text_ac = f"AC Command   : {ac_status} | Temp: {ac_temp}"
        cv2.putText(frame, text_ac, (30, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, status_color, 2)

        out.write(frame)
        cv2.imshow("Smart AC Control System", frame)

        # Terminal log every 15 frames
        if frame_count % 15 == 0:
            print(f"Frame {frame_count:04d} | Raw: {raw_label:13s} -> STABLE: {stable_label:13s} | AC: {ac_status}")

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

finally:
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"\n✅ Finished processing! Saved to: '{output_video_path}'")