import json
import time
from pathlib import Path
import cv2
from ultralytics import YOLO

TARGETS = {"person", "cell phone", "laptop"}
FRAMES_DIR = Path(__file__).parent.parent / "data" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la webcam (dispositivo 0)")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, verbose=False)[0]
    h, w = frame.shape[:2]
    counts = {label: 0 for label in TARGETS}
    detections = []

    for box in results.boxes:
        label = model.names[int(box.cls)]
        if label not in TARGETS:
            continue
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        counts[label] += 1
        detections.append({
            "label": label,
            "conf": round(conf, 4),
            "bbox": [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h],
        })
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    img_path = FRAMES_DIR / f"frame_{int(time.time() * 1000)}.jpg"
    cv2.imwrite(str(img_path), frame)

    print(json.dumps({"frame": str(img_path), "counts": counts, "detections": detections}), flush=True)
    cv2.imshow("Campus Guardian - Detección", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
