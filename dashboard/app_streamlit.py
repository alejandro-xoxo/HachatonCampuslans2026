import sys
import os
import json
from pathlib import Path
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from analytics.aei_engine import calcular_aei
from agent.gemini_agent import analizar_estudiante

# --- Configuración de Página ---
st.set_page_config(page_title="Dashboard AEI - Campus Guardian", layout="wide")

# --- Barra Lateral para Configuración de API Key ---
st.sidebar.title("Configuración de IA")
api_key_env = os.environ.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Google Gemini API Key",
    value=st.session_state.get("gemini_api_key", api_key_env),
    type="password",
    help="Si no tienes la variable de entorno GEMINI_API_KEY en tu sistema, ingrésala aquí."
)
st.session_state["gemini_api_key"] = api_key_input

# --- Intentar cargar estado en tiempo real ---
LIVE_STATE_PATH = Path(__file__).parent.parent / "data" / "live_state.json"

estudiante = {
    "nombre": "Carlos López",
    "asistencia": 75.0,
    "atencion": 60.0,
    "participacion": 55.0,
    "actividades": 80.0,
}
is_live = False
frame_path = None
detections = []
counts = {}
aei = {}

if LIVE_STATE_PATH.exists():
    try:
        with open(LIVE_STATE_PATH, "r") as f:
            live_data = json.load(f)
        
        # Validar consistencia básica
        if "metrics" in live_data and "aei" in live_data:
            estudiante = {
                "nombre": live_data.get("nombre", "Carlos López"),
                "asistencia": live_data["metrics"].get("asistencia", 0.0),
                "atencion": live_data["metrics"].get("atencion", 0.0),
                "participacion": live_data["metrics"].get("participacion", 0.0),
                "actividades": live_data["metrics"].get("actividades", 90.0),
            }
            aei = live_data["aei"]
            frame_path = live_data.get("frame_path")
            detections = live_data.get("detections", [])
            counts = live_data.get("counts", {})
            is_live = True
    except Exception as e:
        # En caso de error de lectura simultánea o JSON incompleto
        pass

if not is_live:
    # Recalcular AEI para datos estáticos
    aei = calcular_aei(
        estudiante["asistencia"],
        estudiante["atencion"],
        estudiante["participacion"],
        estudiante["actividades"],
    )

COLORES = {"verde": "#2ecc71", "amarillo": "#f1c40f", "rojo": "#e74c3c"}
color = COLORES.get(aei["estado"], "#34495e")

# --- UI ---
st.title("📊 Dashboard de Engagement Estudiantil")

if is_live:
    st.success("🟢 Modo en Tiempo Real: Conectado a la Webcam")
else:
    st.warning("⚠️ Modo Simulación: Esperando conexión con la webcam (ejecuta detection_yolo.py)...")

# Diseño de 2 columnas: Izquierda para métricas/análisis, Derecha para feed de cámara
col_left, col_right = st.columns([2, 1.2])

with col_left:
    st.markdown(f"### **Estudiante:** {estudiante['nombre']}")
    st.divider()

    # Score AEI
    st.markdown(
        f"""
        <div style="background-color:{color};padding:20px;border-radius:12px;text-align:center;margin-bottom:20px;">
            <h1 style="color:white;margin:0;">AEI: {aei['score']}</h1>
            <h3 style="color:white;margin:0;">Estado: {aei['estado'].upper()}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Métricas individuales
    st.subheader("Métricas de Engagement")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏫 Asistencia", f"{estudiante['asistencia']:.1f}/100", help="Peso: 20%")
    col2.metric("🧠 Atención", f"{estudiante['atencion']:.1f}/100", help="Peso: 30%")
    col3.metric("🙋 Participación", f"{estudiante['participacion']:.1f}/100", help="Peso: 30%")
    col4.metric("📝 Actividades", f"{estudiante['actividades']:.1f}/100", help="Peso: 20%")
    st.divider()

    # Recomendación Gemini
    st.subheader("🤖 Análisis por IA (Gemini)")
    
    # Preservar recomendación al refrescar
    if "diagnostico_ia" not in st.session_state:
        st.session_state.diagnostico_ia = None

    if st.button("Generar diagnóstico con IA"):
        with st.spinner("Consultando a Gemini..."):
            try:
                resultado = analizar_estudiante({
                    "aei": aei["score"],
                    "estado": aei["estado"],
                    "asistencia": estudiante["asistencia"],
                    "atencion": estudiante["atencion"],
                    "participacion": estudiante["participacion"],
                    "actividades": estudiante["actividades"],
                }, api_key=st.session_state.get("gemini_api_key"))
                st.session_state.diagnostico_ia = resultado
                st.success("✅ Diagnóstico generado")
            except EnvironmentError as e:
                st.error(str(e))
            except Exception as e:
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    st.warning("⚠️ Cuota de Gemini agotada. Mostrando diagnóstico de respaldo.")
                    st.session_state.diagnostico_ia = {
                        "diagnostico": f"El estudiante presenta un AEI de {aei['score']} con estado {aei['estado'].upper()}.",
                        "accion": "Revisar métricas con el tutor asignado.",
                        "recomendacion": "Reforzar participación y atención en clase mediante actividades interactivas."
                    }
                else:
                    st.error(f"Error inesperado: {e}")

    if st.session_state.diagnostico_ia:
        res = st.session_state.diagnostico_ia
        st.markdown(f"**Diagnóstico:** {res.get('diagnostico', 'N/A')}")
        st.markdown(f"**Acción:** {res.get('accion', 'N/A')}")
        st.markdown(f"**Recomendación:** {res.get('recomendacion', 'N/A')}")

with col_right:
    st.subheader("🎥 Vista en Vivo de Cámara")
    if is_live and frame_path and os.path.exists(frame_path):
        st.image(frame_path, use_container_width=True, caption="Frame capturado por la cámara")
        
        # Mostrar conteos rápidos detectados
        st.markdown("#### Objetos en Escena")
        cell_detected = False
        for label, val in counts.items():
            if val > 0:
                if label == "cell phone":
                    st.error(f"🚨 {label.upper()}: {val} (¡Celular detectado!)")
                    cell_detected = True
                elif label == "person":
                    st.success(f"👤 {label.upper()}: {val}")
                else:
                    st.info(f"🔍 {label.upper()}: {val}")
        if not cell_detected and counts.get("person", 0) > 0:
            st.success("✅ Estudiante atento, sin distracciones de celular.")
    else:
        st.info("Sin flujo de cámara activo. Inicia `detection_yolo.py` para visualizar la webcam aquí.")

# --- Auto-refresh de 1 segundo ---
time.sleep(1.0)
st.rerun()
