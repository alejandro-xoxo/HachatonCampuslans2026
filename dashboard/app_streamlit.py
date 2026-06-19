import sys
import os
import json
from pathlib import Path
import time
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from analytics.aei_engine import calcular_aei
from agent.gemini_agent import analizar_estudiante

# --- Configuración de Página (Premium UI) ---
st.set_page_config(
    page_title="Campus Guardian - Dashboard de Engagement",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inyección de CSS Personalizado para Alta Estética ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}
.stApp {
    background-color: #0b0f19;
    color: #f8fafc;
}
.sidebar .sidebar-content {
    background-color: #111827;
}
.metric-box {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 16px;
    border-radius: 10px;
    text-align: center;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
</style>
""", unsafe_allow_html=True)

# --- Motor de Diagnóstico Auxiliar Local (Evita respuestas repetitivas si no hay cuota) ---
def generar_diagnostico_local(datos: dict) -> dict:
    aei = datos["aei"]
    atencion = datos["atencion"]
    participacion = datos["participacion"]
    asistencia = datos["asistencia"]
    
    if asistencia < 20:
        diag = "Estudiante ausente de la sesión de clase o fuera de cuadro."
        acc = "Registrar inasistencia y verificar causa médica o personal."
        rec = "Establecer canal de comunicación directa para evitar deserción por inasistencia continua."
    elif aei < 60:
        diag = "Riesgo académico alto. Engagement general crítico debido a inactividad o distracciones graves."
        if atencion < 50:
            acc = "Llamado de atención inmediato del tutor debido a uso recurrente de celulares o somnolencia."
            rec = "Promover pausas activas de 5 minutos y tutoría de concienciación sobre distractores."
        elif participacion < 50:
            acc = "Programar mentoría de recuperación para revisar la baja entrega de actividades."
            rec = "Involucrar al estudiante en talleres grupales prácticos para elevar su autoconfianza."
        else:
            acc = "Agendar cita con el área de consejería estudiantil."
            rec = "Realizar seguimiento semanal del rendimiento conceptual en clase."
    elif aei < 90:
        diag = "Compromiso académico moderado. Desempeño promedio con variabilidad en atención."
        if atencion < 70:
            acc = "Reubicar al estudiante al frente del aula para minimizar distractores visuales."
            rec = "Estimular la concentración mediante metodologías de aula invertida o preguntas directas."
        elif participacion < 70:
            acc = "Fomentar que exponga o lidere una parte del trabajo de equipo."
            rec = "Asignar roles rotativos dentro del equipo para forzar su interacción académica."
        else:
            acc = "Registrar progreso positivo en el cuaderno de mentorías."
            rec = "Fijar metas de excelencia académica a mediano plazo."
    else:
        diag = "Compromiso académico excepcional. Nivel óptimo de asistencia, atención y participación."
        acc = "Otorgar insignia digital de engagement y felicitación formal."
        rec = "Involucrar al estudiante como monitor o tutor par de sus compañeros."
        
    return {
        "diagnostico": diag,
        "accion": acc,
        "recomendacion": rec
    }

# --- Barra Lateral para Configuración de API Key ---
st.sidebar.title("🛠️ Configuración")
api_key_env = os.environ.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Google Gemini API Key",
    value=st.session_state.get("gemini_api_key", api_key_env),
    type="password",
    help="Si no tienes la variable de entorno GEMINI_API_KEY en tu sistema, ingrésala aquí."
)
st.session_state["gemini_api_key"] = api_key_input

st.sidebar.divider()
st.sidebar.markdown("""
### 💡 Sugerencia para la Demo:
Durante la presentación al jurado:
1. Activa tu webcam con `detection_yolo.py`.
2. Saca tu celular o simula estar distraído.
3. Observa cómo cambian las gráficas en vivo.
4. Genera el diagnóstico para obtener la recomendación de la IA.
""")

# --- Cargar Estado en Tiempo Real ---
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
        # En caso de colisión de lectura/escritura, usa el estado previo guardado
        pass

if not is_live:
    aei = calcular_aei(
        estudiante["asistencia"],
        estudiante["atencion"],
        estudiante["participacion"],
        estudiante["actividades"],
    )

COLORES = {"verde": "#2ecc71", "amarillo": "#f1c40f", "rojo": "#e74c3c"}
color = COLORES.get(aei["estado"], "#34495e")

# --- Guardar Historial en session_state para Gráficos en Vivo ---
if "history" not in st.session_state:
    st.session_state.history = []

# Añadir datos actuales al historial (cada ciclo de recarga de Streamlit)
if is_live:
    st.session_state.history.append({
        "Segundo": len(st.session_state.history) + 1,
        "Atención": estudiante["atencion"],
        "Participación": estudiante["participacion"],
        "AEI": aei["score"]
    })
    # Mantener sólo los últimos 30 registros
    if len(st.session_state.history) > 30:
        st.session_state.history.pop(0)

# --- UI Principal ---
st.title("📊 Campus Guardian Access AI")
st.markdown("### Centro de Monitoreo Académico y Accesibilidad")

if is_live:
    st.success("🟢 Conexión en Vivo Activa: Recibiendo telemetría de la Webcam")
else:
    st.warning("⚠️ Modo Simulación: Esperando telemetría de webcam (Inicia vision/detection_yolo.py)")

st.divider()

# Layout de 2 columnas principales
col_left, col_right = st.columns([1.8, 1.2])

with col_left:
    st.markdown(f"#### 👤 Estudiante: **{estudiante['nombre']}**")
    
    # Marcador de AEI Grande
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, {color} 0%, #1e293b 100%);
                    padding:24px;border-radius:12px;text-align:center;
                    box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); margin-bottom:24px;">
            <h1 style="color:white;margin:0;font-size:3.5rem;font-weight:800;">{aei['score']}</h1>
            <h3 style="color:white;margin:0;font-weight:600;">INDICE DE COMPROMISO ACADÉMICO (AEI)</h3>
            <span style="background-color:rgba(255,255,255,0.2);color:white;padding:4px 12px;
                         border-radius:20px;font-size:0.9rem;font-weight:700;">
                ESTADO: {aei['estado'].upper()}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Columnas de Métricas Individuales
    st.markdown("##### Métricas en Tiempo Real")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🏫 Asistencia", f"{estudiante['asistencia']:.1f}%", help="Peso: 20%")
    m2.metric("🧠 Atención", f"{estudiante['atencion']:.1f}%", help="Peso: 30%")
    m3.metric("🙋 Participación", f"{estudiante['participacion']:.1f}%", help="Peso: 30%")
    m4.metric("📝 Actividades", f"{estudiante['actividades']:.1f}%", help="Peso: 20%")
    
    st.divider()

    # Gráfico Lineal en Vivo
    if is_live and st.session_state.history:
        st.markdown("##### 📈 Curva Dinámica de Engagement (Últimos 30s)")
        df_hist = pd.DataFrame(st.session_state.history)
        st.line_chart(df_hist.set_index("Segundo"))
    else:
        st.info("El gráfico de curvas se activará tan pronto como inicies el script de la webcam.")

with col_right:
    st.markdown("#### 🎥 Feed de Video & Análisis")
    
    # Mostrar webcam
    if is_live and frame_path and os.path.exists(frame_path):
        st.image(frame_path, use_container_width=True, caption="Análisis por Visión de Computadora")
        
        # Objetos detectados en el frame
        st.markdown("##### Objetos y Señales Detectadas:")
        cell_detected = False
        o1, o2 = st.columns(2)
        
        with o1:
            if counts.get("person", 0) > 0:
                st.success(f"👤 Persona en Aula: Sí")
            else:
                st.error("👤 Persona en Aula: Ausente")
                
            if counts.get("laptop", 0) > 0:
                st.info(f"💻 Computadora: Detectada")
        
        with o2:
            if counts.get("cell phone", 0) > 0:
                st.error(f"🚨 Celular: Activo (Distractor)")
                cell_detected = True
            else:
                st.success("🚨 Celular: Ninguno")
                
        if not cell_detected and counts.get("person", 0) > 0:
            st.success("✨ Estudiante enfocado y libre de celulares.")
    else:
        # Imagen de reemplazo estética si la cámara no está lista
        st.markdown(
            """
            <div style="background-color:#1e293b;border:2px dashed #475569;
                        height:250px;border-radius:10px;display:flex;
                        justify-content:center;align-items:center;color:#94a3b8;">
                <span>Esperando conexión con vision/detection_yolo.py...</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # Recomendación IA
    st.markdown("#### 🤖 Diagnóstico Inteligente (Mentor IA)")
    
    if "diagnostico_ia" not in st.session_state:
        st.session_state.diagnostico_ia = None

    if st.button("Analizar con Mentor IA", use_container_width=True):
        datos_para_ia = {
            "aei": aei["score"],
            "estado": aei["estado"],
            "asistencia": estudiante["asistencia"],
            "atencion": estudiante["atencion"],
            "participacion": estudiante["participacion"],
            "actividades": estudiante["actividades"],
        }
        
        if st.session_state.get("gemini_api_key"):
            with st.spinner("Conectando con Gemini 2.0 Flash Lite..."):
                try:
                    resultado = analizar_estudiante(datos_para_ia, api_key=st.session_state["gemini_api_key"])
                    st.session_state.diagnostico_ia = resultado
                    st.success("✅ Diagnóstico generado por Gemini")
                except Exception as e:
                    st.warning("⚠️ Error con la API de Gemini (o cuota agotada). Generando diagnóstico dinámico local...")
                    st.session_state.diagnostico_ia = generar_diagnostico_local(datos_para_ia)
        else:
            with st.spinner("Generando análisis local inteligente..."):
                # Ejecutar motor de reglas local dinámico si no hay clave de API
                time.sleep(0.5)
                st.session_state.diagnostico_ia = generar_diagnostico_local(datos_para_ia)
                st.info("ℹ️ Diagnóstico generado localmente sin clave de API (Modo Offline).")

    if st.session_state.diagnostico_ia:
        res = st.session_state.diagnostico_ia
        
        st.markdown(
            f"""
            <div style="background-color:#0f172a; border-left:4px solid #3b82f6; padding:12px; border-radius:4px; margin-bottom:8px;">
                <strong style="color:#94a3b8;">🔍 Diagnóstico:</strong><br/>
                <span style="color:#f8fafc;">{res.get('diagnostico', 'N/A')}</span>
            </div>
            <div style="background-color:#0f172a; border-left:4px solid #ef4444; padding:12px; border-radius:4px; margin-bottom:8px;">
                <strong style="color:#94a3b8;">⚡ Acción Inmediata:</strong><br/>
                <span style="color:#f8fafc;">{res.get('accion', 'N/A')}</span>
            </div>
            <div style="background-color:#0f172a; border-left:4px solid #10b981; padding:12px; border-radius:4px; margin-bottom:8px;">
                <strong style="color:#94a3b8;">💡 Recomendación Académica:</strong><br/>
                <span style="color:#f8fafc;">{res.get('recomendacion', 'N/A')}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- Auto-refresh de 1 segundo ---
time.sleep(1.0)
st.rerun()
