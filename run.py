#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
import signal
import os

processes = []

def signal_handler(sig, frame):
    print("\n🛑 Deteniendo todos los servicios de Campus Guardian...")
    for p in processes:
        try:
            print(f"Terminando proceso PID {p.pid}...")
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    print("✨ Ecosistema detenido de forma limpia y exitosa.")
    sys.exit(0)

# Registrar manejadores de señales para captura de Ctrl+C
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    print("=" * 70)
    print("🌈 Iniciando Ecosistema de Campus Guardian Access AI")
    print("=" * 70)
    print(f"Utilizando el entorno Python: {sys.executable}\n")

    # 1. Iniciar Servidor del Dashboard (Streamlit)
    print("📊 Iniciando Servidor Dashboard (Streamlit)...")
    cmd_streamlit = [
        sys.executable, "-m", "streamlit", "run",
        "dashboard/app_streamlit.py", "--server.port", "8501"
    ]
    p_streamlit = subprocess.Popen(
        cmd_streamlit,
        stdout=None,  # Imprimir directamente en consola para ver logs de Streamlit
        stderr=None
    )
    processes.append(p_streamlit)
    print(f"👉 Servidor Streamlit iniciado con PID: {p_streamlit.pid}")
    
    # Pequeño delay de cortesía para permitir que Streamlit levante el puerto
    time.sleep(2.5)

    # 2. Iniciar Bucle de Visión Artificial (YOLOv8 + MediaPipe)
    print("\n🎥 Iniciando Bucle de Visión Artificial (Webcam)...")
    cmd_vision = [sys.executable, "vision/detection_yolo.py"]
    p_vision = subprocess.Popen(
        cmd_vision,
        stdout=None,  # Imprimir logs y logs de inferencia en consola
        stderr=None
    )
    processes.append(p_vision)
    print(f"👉 Bucle de Visión YOLO iniciado con PID: {p_vision.pid}")

    print("\n✅ ¡Ecosistema levantado con éxito!")
    print("👉 Abre tu navegador en: http://localhost:8501")
    print("👉 Presiona Ctrl+C para detener ambos procesos de manera limpia.\n")

    # Monitorear activamente los procesos hijos en el hilo principal
    try:
        while True:
            for p in processes:
                # Si alguno de los procesos terminó inesperadamente, detenemos el otro también
                if p.poll() is not None:
                    print(f"\n⚠️ Un proceso ({p.pid}) terminó inesperadamente con código: {p.returncode}")
                    signal_handler(None, None)
            time.sleep(1.0)
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
