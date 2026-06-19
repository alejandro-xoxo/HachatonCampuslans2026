import json
import time
import os
import sys
from pathlib import Path
import cv2
from ultralytics import YOLO

# Agregar la ruta base al path para importar el motor de analítica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analytics.aei_engine import calcular_aei

TARGETS = {"person", "cell phone", "laptop"}
FRAMES_DIR = Path(__file__).parent.parent / "data" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la webcam (dispositivo 0)")

# Historial para calcular medias móviles y simular estabilidad de métricas
history_asistencia = []
history_atencion = []
history_participacion = []
MAX_HISTORY = 60  # aproximadamente los últimos 60 frames

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
        
        # Bounding box normalizado [x, y, w, h] tal como requiere schema.json
        bbox = [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h]
        
        detections.append({
            "label": label,
            "confidence": round(conf, 4),
            "bbox": bbox,
        })
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    # --- Calcular métricas en tiempo real ---
    asistencia_val = 100.0 if counts.get("person", 0) > 0 else 0.0
    
    # Atención disminuye si hay celular o si no está presente
    atencion_val = 0.0 if (counts.get("cell phone", 0) > 0 or asistencia_val == 0.0) else 100.0
    
    # Participación base si está presente, aumenta si usa laptop
    if asistencia_val == 0.0:
        participacion_val = 0.0
    else:
        participacion_val = 85.0 if counts.get("laptop", 0) > 0 else 60.0

    history_asistencia.append(asistencia_val)
    history_atencion.append(atencion_val)
    history_participacion.append(participacion_val)

    if len(history_asistencia) > MAX_HISTORY:
        history_asistencia.pop(0)
        history_atencion.pop(0)
        history_participacion.pop(0)

    avg_asistencia = sum(history_asistencia) / len(history_asistencia)
    avg_atencion = sum(history_atencion) / len(history_atencion)
    avg_participacion = sum(history_participacion) / len(history_participacion)

    aei_res = calcular_aei(avg_asistencia, avg_atencion, avg_participacion, 90.0)

    # Guardar frame físico
    img_path = FRAMES_DIR / f"frame_{int(time.time() * 1000)}.jpg"
    cv2.imwrite(str(img_path), frame)

    # Crear estado unificado conforme al contrato de datos schema.json
    state = {
        "student_id": "carlos_lopez",
        "nombre": "Carlos López",
        "timestamp": str(time.strftime("%Y-%m-%dT%H:%M:%S-05:00")),
        "frame_path": str(img_path),
        "detections": detections,
        "counts": {
            "person": counts.get("person", 0),
            "cell phone": counts.get("cell phone", 0),
            "laptop": counts.get("laptop", 0),
            "hand_raised": 0,
            "drowsy": 0,
            "sign_language": 0
        },
        "metrics": {
            "asistencia": round(avg_asistencia, 2),
            "atencion": round(avg_atencion, 2),
            "participacion": round(avg_participacion, 2),
            "actividades": 90.0
        },
        "aei": aei_res
    }

    # Escritura atómica de live_state.json para evitar lecturas corruptas de Streamlit
    live_state_path = Path(__file__).parent.parent / "data" / "live_state.json"
    temp_state_path = live_state_path.with_suffix(".json.tmp")
    with open(temp_state_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(temp_state_path, live_state_path)

    # Imprimir a stdout para que fiftyone_pipeline pueda seguir leyéndolo en pipe si se desea
    print(json.dumps({
        "frame": str(img_path),
        "counts": counts,
        "detections": [{
            "label": d["label"],
            "conf": d["confidence"],
            "bbox": d["bbox"]
        } for d in detections]
    }), flush=True)

    cv2.imshow("Campus Guardian - Deteccion", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
