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
    page_title="Campus Guardian Access AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inyección de CSS Personalizado para Alta Estética ---
st.markdown("""
<style>
/* Ocultar elementos nativos de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Tipografía y fondo principal */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}
.stApp {
    background-color: #070a13;
    color: #e2e8f0;
}

/* Barra lateral elegante */
[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid #1e293b;
}

/* Modificar las cajas métricas nativas de Streamlit */
div[data-testid="stMetric"] {
    background-color: #0b0f19 !important;
    border: 1px solid #1e293b !important;
    padding: 18px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4) !important;
}
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Motor de Diagnóstico Auxiliar Local ---
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
1. Activa tu webcam con `detection_yolo.py`.
2. Saca tu celular frente a la cámara.
3. Observa la caída en el gráfico de atención.
4. Presiona **Analizar con Mentor IA** para obtener las sugerencias en tiempo real.
""")

# --- Cargar Estado en Tiempo Real ---
LIVE_STATE_PATH = Path(__file__).parent.parent / "data" / "live_state.json"

estudiante_default = {
    "nombre": "Carlos López",
    "asistencia": 75.0,
    "atencion": 60.0,
    "participacion": 55.0,
    "actividades": 80.0,
}
aei_default = calcular_aei(
    estudiante_default["asistencia"],
    estudiante_default["atencion"],
    estudiante_default["participacion"],
    estudiante_default["actividades"],
)

# Inicializar variables de estado persistentes en st.session_state
if "live_estudiante" not in st.session_state:
    st.session_state.live_estudiante = estudiante_default
    st.session_state.live_aei = aei_default
    st.session_state.live_frame_path = None
    st.session_state.live_detections = []
    st.session_state.live_counts = {}
    st.session_state.live_is_live = False
    st.session_state.live_last_update = 0.0

if LIVE_STATE_PATH.exists():
    try:
        # Solo leemos si ha sido modificado recientemente
        mtime = os.path.getmtime(LIVE_STATE_PATH)
        with open(LIVE_STATE_PATH, "r") as f:
            live_data = json.load(f)
        
        if "metrics" in live_data and "aei" in live_data:
            st.session_state.live_estudiante = {
                "nombre": live_data.get("nombre", "Carlos López"),
                "asistencia": live_data["metrics"].get("asistencia", 0.0),
                "atencion": live_data["metrics"].get("atencion", 0.0),
                "participacion": live_data["metrics"].get("participacion", 0.0),
                "actividades": live_data["metrics"].get("actividades", 90.0),
            }
            st.session_state.live_aei = live_data["aei"]
            st.session_state.live_frame_path = live_data.get("frame_path")
            st.session_state.live_detections = live_data.get("detections", [])
            st.session_state.live_counts = live_data.get("counts", {})
            st.session_state.live_is_live = True
            st.session_state.live_last_update = time.time()
    except Exception as e:
        # Si la lectura falla por bloqueo temporal, usamos el estado guardado sin alterarlo
        pass

# Timeout: Si no recibe actualizaciones en 5 segundos, la cámara se considera desconectada
if st.session_state.live_is_live and (time.time() - st.session_state.live_last_update > 5.0):
    st.session_state.live_is_live = False

# Asignar variables finales de renderizado
estudiante = st.session_state.live_estudiante
aei = st.session_state.live_aei
frame_path = st.session_state.live_frame_path
detections = st.session_state.live_detections
counts = st.session_state.live_counts
is_live = st.session_state.live_is_live

COLORES = {"verde": "#10b981", "amarillo": "#f59e0b", "rojo": "#ef4444"}
color = COLORES.get(aei["estado"], "#4b5563")

# --- Guardar Historial en session_state para Gráficos en Vivo ---
if "history" not in st.session_state:
    st.session_state.history = []

if is_live:
    st.session_state.history.append({
        "Segundo": len(st.session_state.history) + 1,
        "Atención": estudiante["atencion"],
        "Participación": estudiante["participacion"],
        "AEI": aei["score"]
    })
    if len(st.session_state.history) > 30:
        st.session_state.history.pop(0)

# --- UI Principal ---
st.title("📊 Campus Guardian Access AI")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -10px;'>Monitoreo de Engagement y Accesibilidad del Aula</p>", unsafe_allow_html=True)

if is_live:
    st.success("🟢 Conexión en vivo activa: Recibiendo datos de la webcam")
else:
    st.warning("⚠️ Modo simulación: Iniciando con datos estáticos (Corre vision/detection_yolo.py)")

st.divider()

col_left, col_right = st.columns([1.8, 1.2])

with col_left:
    st.markdown(f"##### Estudiante: <span style='color: #ffffff; font-weight: 700;'>{estudiante['nombre']}</span>", unsafe_allow_html=True)
    
    # AEI Score Card con borde brillante en lugar de fondo sólido chinchoso
    st.markdown(
        f"""
        <div style="background-color: #0b0f19;
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 24px;
                    text-align: center;
                    box-shadow: 0 0 20px {color}15;
                    margin-bottom: 24px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 3.8rem; font-weight: 800;">{aei['score']}</h1>
            <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.95rem; font-weight: 600; letter-spacing: 1px;">ACADEMIC ENGAGEMENT INDEX (AEI)</p>
            <span style="color: {color}; font-size: 0.9rem; font-weight: 700; border: 1px solid {color}; padding: 3px 12px; border-radius: 20px; display: inline-block; margin-top: 10px;">
                ESTADO: {aei['estado'].upper()}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Métricas Individuales
    st.markdown("<p style='color: #94a3b8; font-weight: 600; margin-bottom: 10px;'>Métricas Analíticas</p>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🏫 Asistencia", f"{estudiante['asistencia']:.1f}%")
    m2.metric("🧠 Atención", f"{estudiante['atencion']:.1f}%")
    m3.metric("🙋 Participación", f"{estudiante['participacion']:.1f}%")
    m4.metric("📝 Actividades", f"{estudiante['actividades']:.1f}%")
    
    st.divider()

    # Gráfico Histórico
    if is_live and st.session_state.history:
        st.markdown("<p style='color: #94a3b8; font-weight: 600; margin-bottom: 10px;'>📈 Curva Dinámica de Engagement (Últimos 30s)</p>", unsafe_allow_html=True)
        df_hist = pd.DataFrame(st.session_state.history)
        st.line_chart(df_hist.set_index("Segundo"))
    else:
        st.info("El gráfico de curvas dinámicas se activará al encender el script de la webcam.")

with col_right:
    st.markdown("##### 🎥 Feed de Cámara")
    
    if is_live and frame_path and os.path.exists(frame_path):
        st.image(frame_path, use_container_width=True)
        
        # Objetos detectados en tarjetas minimalistas
        st.markdown("<p style='color: #94a3b8; font-weight: 600; margin-top: 15px;'>Objetos en Escena</p>", unsafe_allow_html=True)
        cell_detected = False
        o1, o2 = st.columns(2)
        
        with o1:
            if counts.get("person", 0) > 0:
                st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #10b981; font-weight: 600;'>👤 Alumno Presente</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='background-color: #0b0f19; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 600;'>👤 Alumno Ausente</div>", unsafe_allow_html=True)
                
            if counts.get("laptop", 0) > 0:
                st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #60a5fa; font-weight: 600; margin-top: 8px;'>💻 Laptop Activa</div>", unsafe_allow_html=True)
        
        with o2:
            if counts.get("cell phone", 0) > 0:
                st.markdown("<div style='background-color: #ef444415; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700;'>🚨 Celular Activo</div>", unsafe_allow_html=True)
                cell_detected = True
            else:
                st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #94a3b8; font-weight: 600;'>🚨 Sin Celular</div>", unsafe_allow_html=True)
                
        if not cell_detected and counts.get("person", 0) > 0:
            st.markdown("<p style='color: #10b981; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>✨ Atención óptima registrada en este frame</p>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div style="background-color:#0b0f19; border: 1px dashed #1e293b;
                        height: 250px; border-radius: 12px; display: flex;
                        justify-content: center; align-items: center; color: #64748b;">
                <span>Esperando feed de la webcam...</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # Módulo de Mentor IA
    st.markdown("##### 🤖 Análisis del Mentor IA")
    
    if "diagnostico_ia" not in st.session_state:
        st.session_state.diagnostico_ia = None

    if st.button("Analizar comportamiento con IA", use_container_width=True):
        datos_para_ia = {
            "aei": aei["score"],
            "estado": aei["estado"],
            "asistencia": estudiante["asistencia"],
            "atencion": estudiante["atencion"],
            "participacion": estudiante["participacion"],
            "actividades": estudiante["actividades"],
        }
        
        if st.session_state.get("gemini_api_key"):
            with st.spinner("Llamando a Gemini 2.0..."):
                try:
                    resultado = analizar_estudiante(datos_para_ia, api_key=st.session_state["gemini_api_key"])
                    st.session_state.diagnostico_ia = resultado
                    st.success("Diagnóstico generado exitosamente")
                except Exception:
                    st.session_state.diagnostico_ia = generar_diagnostico_local(datos_para_ia)
        else:
            st.session_state.diagnostico_ia = generar_diagnostico_local(datos_para_ia)

    if st.session_state.diagnostico_ia:
        res = st.session_state.diagnostico_ia
        st.markdown(
            f"""
            <div style="background-color: #0b0f19; border: 1px solid #1e293b; border-left: 4px solid #60a5fa; padding: 14px; border-radius: 8px; margin-bottom: 8px;">
                <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Diagnóstico</span><br/>
                <span style="color: #ffffff; font-size: 0.95rem;">{res.get('diagnostico', 'N/A')}</span>
            </div>
            <div style="background-color: #0b0f19; border: 1px solid #1e293b; border-left: 4px solid #ef4444; padding: 14px; border-radius: 8px; margin-bottom: 8px;">
                <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Acción Inmediata</span><br/>
                <span style="color: #ffffff; font-size: 0.95rem;">{res.get('accion', 'N/A')}</span>
            </div>
            <div style="background-color: #0b0f19; border: 1px solid #1e293b; border-left: 4px solid #10b981; padding: 14px; border-radius: 8px; margin-bottom: 8px;">
                <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Recomendación</span><br/>
                <span style="color: #ffffff; font-size: 0.95rem;">{res.get('recomendacion', 'N/A')}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- Auto-refresh de 1 segundo ---
time.sleep(1.0)
st.rerun()
