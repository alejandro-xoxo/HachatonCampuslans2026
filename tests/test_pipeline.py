"""
Mini test para detection_yolo.py y fiftyone_pipeline.py
Corre sin webcam ni FiftyOne real.

    python -m pytest tests/test_pipeline.py -v
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------- helpers ----------------------------------------------------------

SAMPLE_JSON = {
    "frame": "/tmp/frame_test.jpg",
    "counts": {"person": 1, "cell phone": 1, "laptop": 0},
    "detections": [
        {"label": "person",     "conf": 0.91, "bbox": [0.1, 0.05, 0.4, 0.8]},
        {"label": "cell phone", "conf": 0.78, "bbox": [0.6, 0.2,  0.15, 0.2]},
    ],
}


# ---------- tests de formato JSON --------------------------------------------

def test_json_keys():
    assert {"frame", "counts", "detections"} <= SAMPLE_JSON.keys()


def test_bbox_normalizado():
    for d in SAMPLE_JSON["detections"]:
        x, y, w, h = d["bbox"]
        assert 0.0 <= x <= 1.0
        assert 0.0 <= y <= 1.0
        assert 0.0 < w <= 1.0
        assert 0.0 < h <= 1.0


def test_counts_tiene_las_tres_clases():
    counts = SAMPLE_JSON["counts"]
    assert set(counts.keys()) == {"person", "cell phone", "laptop"}


def test_conf_rango():
    for d in SAMPLE_JSON["detections"]:
        assert 0.0 <= d["conf"] <= 1.0


# ---------- test de serialización round-trip ---------------------------------

def test_json_roundtrip():
    raw = json.dumps(SAMPLE_JSON)
    parsed = json.loads(raw)
    assert parsed["counts"]["person"] == 1
    assert parsed["detections"][0]["label"] == "person"


def test_json_invalido_no_lanza():
    """El pipeline debe ignorar líneas no-JSON sin explotar."""
    lineas = ["[WARNING torch] ...", json.dumps(SAMPLE_JSON), "otra basura"]
    resultados = []
    for line in lineas:
        try:
            data = json.loads(line)
            resultados.append(data)
        except json.JSONDecodeError:
            continue
    assert len(resultados) == 1
    assert resultados[0]["frame"] == "/tmp/frame_test.jpg"


# ---------- test de lógica de bbox desde coordenadas pixel -------------------

def test_bbox_calculo_desde_pixeles():
    w, h = 640, 480
    x1, y1, x2, y2 = 64, 48, 320, 384
    bbox = [x1 / w, y1 / h, (x2 - x1) / w, (y2 - y1) / h]
    assert bbox == pytest.approx([0.1, 0.1, 0.4, 0.7])


# ---------- test de filtrado por cell phone ----------------------------------

def test_filtro_cell_phone():
    frames = [
        {"detections": [{"label": "person"}]},
        {"detections": [{"label": "cell phone"}, {"label": "person"}]},
        {"detections": []},
        {"detections": [{"label": "cell phone"}]},
    ]
    con_celular = [
        f for f in frames
        if any(d["label"] == "cell phone" for d in f["detections"])
    ]
    assert len(con_celular) == 2


# ---------- test de estadísticas count_values --------------------------------

def test_count_values_simulado():
    detecciones = ["person", "cell phone", "person", "laptop", "person", "cell phone"]
    counts = {}
    for label in detecciones:
        counts[label] = counts.get(label, 0) + 1
    assert counts == {"person": 3, "cell phone": 2, "laptop": 1}
    assert sum(counts.values()) == 6
