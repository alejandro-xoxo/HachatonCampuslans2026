import os
import sys

# Limitar variables de entorno para evitar contención de hilos y busy-waiting en CPU
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["VECLIB_MAXIMUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

import json
import time
from pathlib import Path
import cv2
import torch
from ultralytics import YOLO

# Limitar hilos en PyTorch a 2 para compatibilidad y fluidez total
torch.set_num_threads(2)

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
frame_counter = 0

# Variables de simulación interactiva para el Pitch / Demo del jurado
sim_drowsy = False
sim_sign = 0  # 0: Ninguno, 1: Pregunta, 2: Ayuda, 3: Terminado
sim_absent = False

SIGN_TEXTS = {
    0: "",
    1: "Tengo una pregunta / Solicito participar",
    2: "Necesito ayuda con el codigo / Soporte",
    3: "Termine el ejercicio / Avance completado"
}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionar el frame de captura a 640x480 para ahorrar CPU
    frame = cv2.resize(frame, (640, 480))

    # Inferencia optimizada a imgsz=320 (3x a 4x más veloz en CPU de 8.ª generación)
    results = model(frame, imgsz=320, verbose=False)[0]
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

    # --- Calcular métricas en tiempo real aplicando modificadores de simulación ---
    person_count = 0 if sim_absent else counts.get("person", 0)
    asistencia_val = 100.0 if person_count > 0 else 0.0
    
    # Atención disminuye si hay celular, si simula somnolencia o si no está presente
    atencion_val = 100.0
    if sim_drowsy or counts.get("cell phone", 0) > 0 or asistencia_val == 0.0:
        atencion_val = 0.0
    
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

    # Guardar frame en vivo para Streamlit (sobrescribir el mismo archivo para evitar latencia de I/O)
    live_img_path = Path(__file__).parent.parent / "data" / "live_frame.jpg"
    cv2.imwrite(str(live_img_path), frame)

    # Solo guardamos el frame histórico y lo enviamos al pipeline de FiftyOne cada N frames
    frame_counter += 1
    should_save_historic = (frame_counter % 10 == 0)

    img_path = live_img_path
    if should_save_historic:
        historic_path = FRAMES_DIR / f"frame_{int(time.time() * 1000)}.jpg"
        cv2.imwrite(str(historic_path), frame)
        img_path = historic_path

        # Imprimir a stdout para que pipeline lea histórico
        print(json.dumps({
            "frame": str(historic_path),
            "counts": counts,
            "detections": [{
                "label": d["label"],
                "conf": d["confidence"],
                "bbox": d["bbox"]
            } for d in detections]
        }), flush=True)

    # Crear estado unificado conforme al contrato de datos schema.json
    state = {
        "student_id": "carlos_lopez",
        "nombre": "Carlos López",
        "timestamp": str(time.strftime("%Y-%m-%dT%H:%M:%S-05:00")),
        "frame_path": str(img_path),
        "detections": detections,
        "counts": {
            "person": person_count,
            "cell phone": counts.get("cell phone", 0),
            "laptop": counts.get("laptop", 0),
            "hand_raised": 0,
            "drowsy": 1 if sim_drowsy else 0,
            "sign_language": 1 if sim_sign > 0 else 0
        },
        "metrics": {
            "asistencia": round(avg_asistencia, 2),
            "atencion": round(avg_atencion, 2),
            "participacion": round(avg_participacion, 2),
            "actividades": 90.0
        },
        "aei": aei_res,
        "transcript": SIGN_TEXTS[sim_sign] if sim_sign > 0 else ""
    }

    # Escritura atómica de live_state.json para evitar lecturas corruptas de Streamlit
    live_state_path = Path(__file__).parent.parent / "data" / "live_state.json"
    temp_state_path = live_state_path.with_suffix(".json.tmp")
    with open(temp_state_path, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(temp_state_path, live_state_path)

    # Dibujar info de simulación en la ventana de OpenCV para guiar al presentador
    cv2.putText(frame, "TECLAS DEMO:", (10, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, f"[D] Somnolencia: {'SI' if sim_drowsy else 'NO'}", (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255) if sim_drowsy else (0, 255, 0), 1)
    cv2.putText(frame, f"[S] Senas: {SIGN_TEXTS[sim_sign] if sim_sign > 0 else 'NO'}", (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0) if sim_sign > 0 else (0, 255, 0), 1)
    cv2.putText(frame, f"[A] Ausencia: {'SI' if sim_absent else 'NO'}", (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255) if sim_absent else (0, 255, 0), 1)

    cv2.imshow("Campus Guardian - Deteccion", frame)

    # Introducir delay para 5 FPS
    time.sleep(0.2)

    # Captura de teclado local
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("d"):
        sim_drowsy = not sim_drowsy
    elif key == ord("s"):
        sim_sign = (sim_sign + 1) % 4
    elif key == ord("a"):
        sim_absent = not sim_absent

cap.release()
cv2.destroyAllWindows()
