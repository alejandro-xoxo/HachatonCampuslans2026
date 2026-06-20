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
import mediapipe as mp

# Limitar hilos en PyTorch a 2 para compatibilidad y fluidez total
torch.set_num_threads(2)

# Agregar la ruta base al path para importar el motor de analítica
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analytics.aei_engine import calcular_aei

# Intentar inicializar MediaPipe Face Mesh para detección de somnolencia
USE_MEDIAPIPE = False
try:
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        USE_MEDIAPIPE = True
except Exception:
    pass

# Si MediaPipe no está completamente disponible en este entorno, usar los cascadas de OpenCV como fallback
if not USE_MEDIAPIPE:
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    except Exception:
        pass

TARGETS = {"person", "cell phone", "laptop"}
FRAMES_DIR = Path(__file__).parent.parent / "data" / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

# Bandera para guardar frames históricos en disco (desactivado por defecto para ahorrar E/S y almacenamiento)
SAVE_HISTORIC_FRAMES = False

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la webcam (dispositivo 0)")

# Historial para calcular medias móviles y simular estabilidad de métricas
# Inicializamos con 0.0 para que el score en cada sesión comience en cero y crezca gradualmente
MAX_HISTORY = 60  # aproximadamente los últimos 60 frames
history_asistencia = [0.0] * MAX_HISTORY
history_atencion = [0.0] * MAX_HISTORY
history_participacion = [0.0] * MAX_HISTORY
history_actividades = [0.0] * MAX_HISTORY
frame_counter = 0
drowsy_frames = 0  # Contador de frames con ojos cerrados para detectar somnolencia real

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

# Variables para optimizar rendimiento: Ejecutar inferencia YOLO cada N frames
YOLO_INTERVAL = 4
cached_detections = []
cached_counts = {label: 0 for label in TARGETS}

# Variables para optimizar rendimiento de somnolencia: Ejecutar cada 2 frames y cachear marcas visuales
DROWSY_INTERVAL = 2
cached_drowsy_real = False
cached_ear_val = 0.0
cached_faces_to_draw = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Redimensionar el frame de captura a 640x480 para ahorrar CPU
    frame = cv2.resize(frame, (640, 480))
    h, w = frame.shape[:2]

    # Ejecutar YOLOv8 solo cada YOLO_INTERVAL frames para ahorrar CPU drásticamente y mejorar la fluidez
    if frame_counter % YOLO_INTERVAL == 0 or not cached_detections:
        results = model(frame, imgsz=320, conf=0.30, verbose=False)[0]
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
        cached_detections = detections
        cached_counts = counts
    else:
        detections = cached_detections
        counts = cached_counts

    # Dibujar las detecciones (reales o cacheadas) en el frame actual
    for d in detections:
        bbox = d["bbox"]
        label = d["label"]
        conf = d["confidence"]
        x1, y1 = int(bbox[0] * w), int(bbox[1] * h)
        x2, y2 = int((bbox[0] + bbox[2]) * w), int((bbox[1] + bbox[3]) * h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (124, 58, 237), 2) # Color morado #7c3aed
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (124, 58, 237), 2)

    # --- Detección real de somnolencia (MediaPipe con Fallback a OpenCV Haar Cascades) ---
    if frame_counter % DROWSY_INTERVAL == 0 or 'cached_drowsy_real' not in locals():
        drowsy_real = False
        ear_val = 0.0
        faces_to_draw = []
        
        if USE_MEDIAPIPE:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                fm_results = face_mesh.process(rgb_frame)
                if fm_results.multi_face_landmarks:
                    landmarks = fm_results.multi_face_landmarks[0].landmark
                    
                    # Ojo izquierdo: superior=159, inferior=145, lateral_izq=33, lateral_der=133
                    p159, p145, p33, p133 = landmarks[159], landmarks[145], landmarks[33], landmarks[133]
                    dist_left_y = ((p159.x - p145.x)**2 + (p159.y - p145.y)**2)**0.5
                    dist_left_x = ((p33.x - p133.x)**2 + (p33.y - p133.y)**2)**0.5
                    ear_left = dist_left_y / (dist_left_x if dist_left_x > 0 else 1.0)
                    
                    # Ojo derecho: superior=386, inferior=374, lateral_izq=362, lateral_der=263
                    p386, p374, p362, p263 = landmarks[386], landmarks[374], landmarks[362], landmarks[263]
                    dist_right_y = ((p386.x - p374.x)**2 + (p386.y - p374.y)**2)**0.5
                    dist_right_x = ((p362.x - p263.x)**2 + (p362.y - p263.y)**2)**0.5
                    ear_right = dist_right_y / (dist_right_x if dist_right_x > 0 else 1.0)
                    
                    ear_val = (ear_left + ear_right) / 2.0
                    
                    # Guardar landmarks de los ojos para dibujar
                    eye_pts = []
                    for idx in [159, 145, 33, 133, 386, 374, 362, 263]:
                        pt = landmarks[idx]
                        eye_pts.append((int(pt.x * w), int(pt.y * h)))
                    faces_to_draw = [{"type": "mediapipe", "points": eye_pts}]
                    
                    if ear_val < 0.15:
                        drowsy_frames += 1
                    else:
                        drowsy_frames = max(0, drowsy_frames - 1)
                        
                    if drowsy_frames >= 5:
                        drowsy_real = True
                else:
                    drowsy_frames = max(0, drowsy_frames - 1)
            except Exception:
                pass
        else:
            # Fallback usando OpenCV Haar Cascades optimizado (downscaling a 320x240)
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Redimensionar a la mitad para que sea 4x más rápido de procesar en CPU
                gray_small = cv2.resize(gray, (320, 240))
                faces = face_cascade.detectMultiScale(gray_small, 1.25, 4)
                
                if len(faces) == 0:
                    drowsy_frames = max(0, drowsy_frames - 1)
                    
                for (fx, fy, fw, fh) in faces:
                    roi_gray = gray_small[fy:fy+fh, fx:fx+fw]
                    
                    # Detectar ojos en la región de interés pequeña (ROI)
                    eyes = eye_cascade.detectMultiScale(roi_gray, 1.15, 3)
                    
                    # Guardar cara y ojos escalados de vuelta a 640x480
                    eyes_scaled = []
                    for (ex, ey, ew, eh) in eyes:
                        # Coordenadas relativas a la ROI escaladas de vuelta a 640x480 (multiplicando por 2)
                        ex_scaled = (fx + ex + ew // 2) * 2
                        ey_scaled = (fy + ey + eh // 2) * 2
                        r_scaled = (min(ew, eh) // 2) * 2
                        eyes_scaled.append((ex_scaled, ey_scaled, r_scaled))
                        
                    faces_to_draw.append({
                        "type": "cascade",
                        "face_rect": (fx * 2, fy * 2, fw * 2, fh * 2),
                        "eyes": eyes_scaled
                    })
                    
                    # Si se detecta cara pero no se detectan ambos ojos, asumimos ojos cerrados
                    if len(eyes) < 2:
                        drowsy_frames += 1
                    else:
                        drowsy_frames = max(0, drowsy_frames - 1)
                        
                    if drowsy_frames >= 5:
                        drowsy_real = True
            except Exception:
                pass
                
        cached_drowsy_real = drowsy_real
        cached_ear_val = ear_val
        cached_faces_to_draw = faces_to_draw
    else:
        drowsy_real = cached_drowsy_real
        ear_val = cached_ear_val
        faces_to_draw = cached_faces_to_draw

    # --- Dibujar las marcas visuales de somnolencia en cada frame ---
    for item in faces_to_draw:
        if item["type"] == "mediapipe":
            for pt in item["points"]:
                cv2.circle(frame, pt, 2, (255, 0, 255), -1)
        elif item["type"] == "cascade":
            fx_c, fy_c, fw_c, fh_c = item["face_rect"]
            cv2.rectangle(frame, (fx_c, fy_c), (fx_c+fw_c, fy_c+fh_c), (255, 0, 255), 1)
            for (ex_c, ey_c, r_c) in item["eyes"]:
                cv2.circle(frame, (ex_c, ey_c), r_c, (0, 255, 255), 1)

    if USE_MEDIAPIPE and ear_val > 0:
        cv2.putText(frame, f"EAR: {ear_val:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

    # --- Calcular métricas en tiempo real aplicando modificadores de simulación ---
    person_count = 0 if sim_absent else counts.get("person", 0)
    asistencia_val = 100.0 if person_count > 0 else 0.0
    
    # Drowsiness activa si es real o si está forzada por teclado (solo si está presente)
    drowsy_active = (drowsy_real or sim_drowsy) and (asistencia_val > 0.0)
    
    # Atención disminuye si hay celular, si simula/detecta somnolencia o si no está presente
    atencion_val = 100.0
    if drowsy_active or counts.get("cell phone", 0) > 0 or asistencia_val == 0.0:
        atencion_val = 0.0
    
    # Participación base si está presente, aumenta si usa laptop
    if asistencia_val == 0.0:
        participacion_val = 0.0
    else:
        participacion_val = 85.0 if counts.get("laptop", 0) > 0 else 60.0

    # Actividades también es dinámica: empieza en 0.0 y sube a 90.0 si está presente
    actividades_val = 90.0 if asistencia_val > 0.0 else 0.0

    history_asistencia.append(asistencia_val)
    history_atencion.append(atencion_val)
    history_participacion.append(participacion_val)
    history_actividades.append(actividades_val)

    if len(history_asistencia) > MAX_HISTORY:
        history_asistencia.pop(0)
        history_atencion.pop(0)
        history_participacion.pop(0)
        history_actividades.pop(0)

    avg_asistencia = sum(history_asistencia) / len(history_asistencia)
    avg_atencion = sum(history_atencion) / len(history_atencion)
    avg_participacion = sum(history_participacion) / len(history_participacion)
    avg_actividades = sum(history_actividades) / len(history_actividades)

    aei_res = calcular_aei(avg_asistencia, avg_atencion, avg_participacion, avg_actividades)

    # Guardar frame en vivo para Streamlit (sobrescribir el mismo archivo para evitar latencia de I/O)
    live_img_path = Path(__file__).parent.parent / "data" / "live_frame.jpg"
    cv2.imwrite(str(live_img_path), frame)

    # Solo guardamos el frame histórico y lo enviamos al pipeline de FiftyOne cada N frames si la bandera está habilitada
    frame_counter += 1
    should_save_historic = SAVE_HISTORIC_FRAMES and (frame_counter % 10 == 0)

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
            "drowsy": 1 if drowsy_active else 0,
            "sign_language": 1 if sim_sign > 0 else 0
        },
        "metrics": {
            "asistencia": round(avg_asistencia, 2),
            "atencion": round(avg_atencion, 2),
            "participacion": round(avg_participacion, 2),
            "actividades": round(avg_actividades, 2)
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
    cv2.putText(frame, f"[D] Somnolencia Sim: {'SI' if sim_drowsy else 'NO'} | Real EAR: {ear_val:.2f}", (10, h - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255) if drowsy_active else (0, 255, 0), 1)
    cv2.putText(frame, f"[S] Senas: {SIGN_TEXTS[sim_sign] if sim_sign > 0 else 'NO'}", (10, h - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0) if sim_sign > 0 else (0, 255, 0), 1)
    cv2.putText(frame, f"[A] Ausencia Sim: {'SI' if sim_absent else 'NO'}", (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255) if sim_absent else (0, 255, 0), 1)

    cv2.imshow("Campus Guardian - Deteccion", frame)

    # Pequeño delay de cortesía de 10ms para evitar busy-waiting extremo, permitiendo FPS máximos
    time.sleep(0.01)

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
