import cv2
import numpy as np
import onnxruntime as ort

model_path = "model.onnx"
video_path = "IMG_8799.MOV"

# 1. Load ONNX Model & Print Inputs
session = ort.InferenceSession(model_path)
input_info = session.get_inputs()[0]

print("=" * 60)
print("🔍 ONNX MODEL DIAGNOSTIC DETAILS")
print(f"Input Name  : {input_info.name}")
print(f"Input Shape : {input_info.shape}")
print(f"Input Type  : {input_info.type}")
print("=" * 60)

# 2. Read Frame 1 from Video
cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()
cap.release()

if not ret:
    print("❌ ERROR: Video file එක read කරගන්න බැරි වුනා!")
    exit()

# Save sample frame to verify image reading
cv2.imwrite("debug_sample_frame.jpg", frame)
print("\n📸 Video එකේ පළමු Frame එක 'debug_sample_frame.jpg' ලෙස Save වුනා.\n")

def test_preprocessing_mode(frame, mode, shape):
    img = cv2.resize(frame, (224, 224))
    
    if mode == 1: # RGB 0-255 Float
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
    elif mode == 2: # RGB 0-1 Float
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    elif mode == 3: # BGR 0-255 Float
        img = img.astype(np.float32)
    elif mode == 4: # RGB + Mean Subtraction (Azure Standard)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        mean = np.array([123.68, 116.78, 103.94], dtype=np.float32)
        img = img - mean

    # NCHW Format Check
    if len(shape) == 4 and (shape[1] == 3 or shape[1] == '3'):
        img = np.transpose(img, (2, 0, 1))

    img = np.expand_dims(img, axis=0)
    
    outputs = session.run(None, {input_info.name: img})
    return outputs

modes = [
    (1, "1. RGB (0 - 255 Range)"),
    (2, "2. RGB (0 - 1 Normalized)"),
    (3, "3. BGR (0 - 255 Raw)"),
    (4, "4. RGB + Azure Mean Subtraction")
]

print("🧪 TESTING ALL PREPROCESSING MODES ON FRAME 1:\n")

for mode_id, mode_name in modes:
    try:
        res = test_preprocessing_mode(frame, mode_id, input_info.shape)
        predicted_label = res[0][0]
        scores = res[1][0] if len(res) > 1 else "No Scores"
        print(f"➡️ Mode {mode_id}: {mode_name}")
        print(f"   Top Label Output: {predicted_label}")
        print(f"   Raw Probabilities: {scores}\n")
    except Exception as e:
        print(f"❌ Mode {mode_id} Failed: {e}\n")