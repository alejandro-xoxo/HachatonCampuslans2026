"""
Uso:
    python vision/detection_yolo.py | python fiftyone_app/fiftyone_pipeline.py
"""
import json
import sys

import fiftyone as fo
from fiftyone import ViewField as F

DATASET_NAME = "campus_distracciones"

if fo.dataset_exists(DATASET_NAME):
    fo.delete_dataset(DATASET_NAME)
dataset = fo.Dataset(DATASET_NAME)

print("[pipeline] Recibiendo frames... Presiona Ctrl+C para detener y abrir FiftyOne", file=sys.stderr)

try:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue  # ignora líneas no-JSON (warnings de torch/ultralytics)

        img_path = data.get("frame")
        detections = data.get("detections", [])

        if not img_path:
            continue

        fo_detections = [
            fo.Detection(
                label=d["label"],
                confidence=d["conf"],
                bounding_box=d["bbox"],
            )
            for d in detections
        ]

        sample = fo.Sample(
            filepath=img_path,
            detections=fo.Detections(detections=fo_detections),
            counts=data.get("counts", {}),
        )
        dataset.add_sample(sample)
        print(f"[pipeline] +1 sample ({len(dataset)} total)", file=sys.stderr)

except KeyboardInterrupt:
    pass

print(f"\n[pipeline] Dataset '{DATASET_NAME}': {len(dataset)} samples", file=sys.stderr)

if len(dataset) == 0:
    print("[pipeline] Sin samples, no se lanza la app.", file=sys.stderr)
    sys.exit(0)

# --- Estadísticas para el pitch ---
print("\n==============================")
print("  ESTADÍSTICAS DE DETECCIÓN")
print("==============================")
label_counts = dataset.count_values("detections.detections.label")
for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f"  {label:<12} {count:>4} detecciones")
print(f"  {'TOTAL':<12} {sum(label_counts.values()):>4} detecciones")
print(f"  {'FRAMES':<12} {len(dataset):>4} procesados")
print("==============================\n")

# --- Vista: solo frames con celular ---
cellphone_view = dataset.filter_labels(
    "detections", F("label") == "cell phone"
).match(F("detections.detections").length() > 0)

print(f"[pipeline] Frames con celular detectado: {len(cellphone_view)}")
print(f"[pipeline] Frames sin distracciones:     {len(dataset) - len(cellphone_view)}")

# --- Lanzar app mostrando la vista de celulares ---
session = fo.launch_app(view=cellphone_view if len(cellphone_view) > 0 else dataset)
print("\n[pipeline] App abierta en http://localhost:5151")
print("[pipeline] Mostrando vista: frames con 'cell phone'")
print("[pipeline] Para ver el dataset completo ejecuta en otra terminal:")
print("              python -c \"import fiftyone as fo; fo.launch_app(fo.load_dataset('campus_distracciones'))\"")
input("\nPresiona Enter para cerrar...\n")
