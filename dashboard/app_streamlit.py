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
    page_icon="🌈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Inyección de CSS Personalizado ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Deep space gradient background */
.stApp {
    background: radial-gradient(circle at 50% 50%, #0d0926 0%, #050310 100%) !important;
    color: #f1f5f9 !important;
    animation: fadeIn 1.0s ease-out;
}

/* Sidebar styling - Purple tint */
[data-testid="stSidebar"] {
    background-color: #080518 !important;
    border-right: 1px solid rgba(139, 92, 246, 0.25) !important;
    box-shadow: 2px 0 15px rgba(0, 0, 0, 0.5) !important;
}

/* Glowing card effect for Metrics */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d0b26 0%, #120e36 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.25) !important;
    padding: 18px !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 32px 0 rgba(139, 92, 246, 0.05), inset 0 0 8px rgba(59, 130, 246, 0.05) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideUp 0.6s ease-out;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(6, 182, 212, 0.5) !important;
    box-shadow: 0 12px 24px rgba(139, 92, 246, 0.15), inset 0 0 12px rgba(6, 182, 212, 0.15) !important;
}

div[data-testid="stMetric"] label {
    color: #c084fc !important; /* Soft Purple */
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
}

div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #06b6d4 !important; /* Cyber Cyan */
    font-size: 2.0rem !important;
    font-weight: 800 !important;
    text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

/* Custom buttons style (Purple to Blue gradient) */
div.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #2563eb 100%) !important;
    color: #ffffff !important;
    border: none !important;
    padding: 10px 24px !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    letter-spacing: 0.5px;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%) !important;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5) !important;
    transform: translateY(-2px);
}

div.stButton > button:active {
    transform: translateY(1px);
}

/* Interactive elements and text gradients */
h1 {
    background: linear-gradient(135deg, #c084fc 0%, #60a5fa 100%) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-weight: 800 !important;
}

h2, h3 {
    color: #e2e8f0 !important;
    font-weight: 700 !important;
}

/* Tabs customization */
button[data-baseweb="tab"] {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: #94a3b8 !important;
    background-color: transparent !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.3s ease !important;
}

button[data-baseweb="tab"]:hover {
    color: #c084fc !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #a855f7 !important;
    border-bottom-color: #a855f7 !important;
    text-shadow: 0 0 10px rgba(168, 85, 247, 0.3);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
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
        diag = "Riesgo académico alto. Engagement crítico debido a inactividad o distracciones graves."
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

modo_manual = False

st.sidebar.divider()
st.sidebar.title("🛑 Acciones Globales")
if st.sidebar.button("🔴 Detener Todo el Sistema", help="Detiene los procesos de la cámara web (YOLO) y apaga este servidor de Streamlit"):
    st.sidebar.warning("Apagando sensores de cámara y deteniendo servidor Streamlit...")
    try:
        import psutil
        # Detener procesos de visión YOLO y base de datos FiftyOne de manera multiplataforma (Windows/Linux/macOS)
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmd = proc.info.get('cmdline')
                if cmd:
                    cmd_str = " ".join(cmd)
                    if "detection_yolo.py" in cmd_str or "fiftyone_pipeline.py" in cmd_str:
                        proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception:
        pass
    
    # Cerrar el propio proceso del servidor Streamlit
    import os
    import signal
    time.sleep(1.0)
    os.kill(os.getpid(), signal.SIGINT)



# --- Cargar Estado en Tiempo Real ---
LIVE_STATE_PATH = Path(__file__).parent.parent / "data" / "live_state.json"

# Función para crear un frame placeholder si no existe live_frame.jpg
def asegurar_placeholder_frame():
    live_img_path = Path(__file__).parent.parent / "data" / "live_frame.jpg"
    if not live_img_path.exists():
        try:
            import numpy as np
            import cv2
            # Crear una imagen de 480x640 con fondo azul oscuro premium
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img[:] = [19, 10, 7] # BGR para #070a13
            
            # Dibujar un marco cian/azul holográfico
            cv2.rectangle(img, (20, 20), (620, 460), [250, 165, 96], 1)
            
            # Dibujar marcas de enfoque en las esquinas
            # Superior Izquierda
            cv2.line(img, (30, 30), (50, 30), [250, 165, 96], 2)
            cv2.line(img, (30, 30), (30, 50), [250, 165, 96], 2)
            # Superior Derecha
            cv2.line(img, (610, 30), (590, 30), [250, 165, 96], 2)
            cv2.line(img, (610, 30), (610, 50), [250, 165, 96], 2)
            # Inferior Izquierda
            cv2.line(img, (30, 450), (50, 450), [250, 165, 96], 2)
            cv2.line(img, (30, 450), (30, 430), [250, 165, 96], 2)
            # Inferior Derecha
            cv2.line(img, (610, 450), (590, 450), [250, 165, 96], 2)
            cv2.line(img, (610, 450), (610, 430), [250, 165, 96], 2)
            
            # Dibujar un círculo de rec en rojo
            cv2.circle(img, (50, 50), 6, [68, 68, 239], -1) # BGR para #ef4444
            cv2.putText(img, "REC STANDBY", (65, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.4, [148, 163, 184], 1, cv2.LINE_AA)
            
            # Textos informativos
            cv2.putText(img, "CAMPUS GUARDIAN AI", (170, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, [255, 255, 255], 2, cv2.LINE_AA)
            cv2.putText(img, "ESPERANDO WEBCAM...", (210, 245), cv2.FONT_HERSHEY_SIMPLEX, 0.55, [250, 165, 96], 1, cv2.LINE_AA)
            cv2.putText(img, "Inicie vision/detection_yolo.py para conectar la camara", (110, 290), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, [148, 163, 184], 1, cv2.LINE_AA)
            
            # Asegurar directorio de datos y escribir imagen
            live_img_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(live_img_path), img)
        except Exception:
            pass

# Crear el frame placeholder al arrancar el dashboard
asegurar_placeholder_frame()

estudiante_default = {
    "nombre": "Carlos López",
    "asistencia": 0.0,
    "atencion": 0.0,
    "participacion": 0.0,
    "actividades": 0.0,
}
aei_default = calcular_aei(
    estudiante_default["asistencia"],
    estudiante_default["atencion"],
    estudiante_default["participacion"],
    estudiante_default["actividades"],
)

# Inicializar st.session_state
if "live_estudiante" not in st.session_state:
    st.session_state.live_estudiante = estudiante_default
    st.session_state.live_aei = aei_default
    st.session_state.live_frame_path = str(LIVE_STATE_PATH.parent / "live_frame.jpg")
    st.session_state.live_detections = []
    st.session_state.live_counts = {}
    st.session_state.live_is_live = False
    st.session_state.live_last_update = 0.0
    st.session_state.live_transcript = ""
    st.session_state.profesor_subtitles = ""

if "profesor_log" not in st.session_state:
    st.session_state.profesor_log = []

def cargar_estado_en_vivo():
    # Simulación manual eliminada. Todo se basa en el feed de visión real en vivo.
    
    # Modo normal (leer archivo)
    estudiante = estudiante_default
    aei = aei_default
    frame_path = str(LIVE_STATE_PATH.parent / "live_frame.jpg")
    detections = []
    counts = {}
    is_live = False
    transcript = ""
    
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
                frame_path = str(LIVE_STATE_PATH.parent / "live_frame.jpg")
                detections = live_data.get("detections", [])
                counts = live_data.get("counts", {})
                
                # Está en vivo si el archivo tiene menos de 5 segundos de antigüedad
                mtime = LIVE_STATE_PATH.stat().st_mtime
                if time.time() - mtime < 5.0:
                    is_live = True
                transcript = live_data.get("transcript", "")
        except Exception:
            pass
            
    return estudiante, aei, frame_path, detections, counts, is_live, transcript

# --- Cargar Estado Inicial para UI Global ---
estudiante, aei, frame_path, detections, counts, is_live, transcript = cargar_estado_en_vivo()

# Historial para gráficos
if "history" not in st.session_state or not st.session_state.history:
    # Inicializamos con un punto en cero para que empiece limpio
    st.session_state.history = [
        {"Segundo": 0, "Atención": 0.0, "Participación": 0.0, "AEI": 0.0}
    ]

# --- UI Principal ---
st.title("🌈 Campus Guardian Access AI")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -10px;'>Plataforma Inteligente de Inclusión y Alerta Temprana Académica</p>", unsafe_allow_html=True)

# Barra de estado dinámica (Fragmento)
@st.fragment(run_every=2.0)
def render_status_bar():
    _, _, _, _, _, is_live_dynamic, _ = cargar_estado_en_vivo()
    if is_live_dynamic:
        st.success("🟢 Conexión en vivo activa: Recibiendo datos de la webcam")
    else:
        st.warning("⚠️ Modo offline: Iniciando con datos estáticos (Corre run.py para activar la cámara en vivo)")

render_status_bar()

st.divider()

# Crear Pestañas: Aula Inclusiva y Analítica Engagement
tab_inclusiva, tab_engagement = st.tabs(["🙋 Aula Inclusiva (Accesibilidad)", "📊 Analítica de Engagement (AEI)"])

# ----------------- PESTAÑA AULA INCLUSIVA -----------------
with tab_inclusiva:
    col_inc_left, col_inc_right = st.columns([1.6, 1.4])
    
    with col_inc_left:
        st.markdown("### 🔊 Comunicación Bidireccional Inclusiva")
        
        # Subtítulos: Profesor -> Estudiante Sordo
        st.markdown("##### 1. Profesor ➔ Estudiante Sordo (Subtítulos Whisper STT)")
        
        # Simulador de Habla
        st.markdown("<p style='color: #94a3b8; font-size: 0.9rem; margin-bottom: 5px;'>Simular dictado del docente (presione para dictar frase):</p>", unsafe_allow_html=True)
        
        # Grid de Presets
        p_col1, p_col2 = st.columns(2)
        frases_presets = [
            ("👋 Inicio de clase", "Buenos días clase, hoy implementaremos buenas prácticas de programación en Python."),
            ("💻 Ejercicio práctico", "Por favor abran su laptop para resolver el laboratorio de detección de objetos."),
            ("❓ Consulta de dudas", "¿Alguien tiene alguna pregunta sobre el código o la lógica de control del sistema?"),
            ("📱 Regla de distractores", "Por favor, eviten el uso de teléfonos celulares para mantener el enfoque en la clase."),
            ("🤟 Recordatorio de señas", "Recuerden usar señas ante la cámara si necesitan ayuda o si han completado el ejercicio."),
            ("🤖 Cierre y Mentor IA", "Excelente avance, realizaremos el análisis de engagement académico con el Mentor IA.")
        ]
        
        for i, (label, texto_frase) in enumerate(frases_presets):
            col_target = p_col1 if i % 2 == 0 else p_col2
            if col_target.button(label, key=f"preset_{i}", use_container_width=True):
                st.session_state.profesor_subtitles = texto_frase
                t_str = time.strftime("%H:%M:%S")
                st.session_state.profesor_log.insert(0, f"[{t_str}] Profesor: {texto_frase}")
                if len(st.session_state.profesor_log) > 5:
                    st.session_state.profesor_log.pop()
                st.rerun()
                
        # Entrada libre
        profesor_input = st.text_input(
            "O escribe una frase libre del Profesor y presiona Enter:",
            placeholder="Escribe aquí lo que el profesor está diciendo y presiona Enter...",
            key="profesor_free_text"
        )
        if profesor_input:
            if "last_free_input" not in st.session_state or st.session_state.last_free_input != profesor_input:
                st.session_state.profesor_subtitles = profesor_input
                st.session_state.last_free_input = profesor_input
                t_str = time.strftime("%H:%M:%S")
                st.session_state.profesor_log.insert(0, f"[{t_str}] Profesor: {profesor_input}")
                if len(st.session_state.profesor_log) > 5:
                    st.session_state.profesor_log.pop()
                st.rerun()

        # Display y Historial dinámico (Fragmento)
        @st.fragment(run_every=0.2)
        def render_subtitles_display():
            if st.session_state.profesor_subtitles:
                st.markdown(
                    f"""
                    <div style="background-color: #0b0f19; border: 2px dashed #10b981; padding: 15px; border-radius: 10px; text-align: center; margin-top: 10px; margin-bottom: 10px;">
                        <span style="color: #10b981; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">PANTALLA DEL ESTUDIANTE (Subtítulos en Vivo)</span><br/>
                        <span style="color: #ffffff; font-size: 1.25rem; font-weight: 700; display: inline-block; margin-top: 5px;">"{st.session_state.profesor_subtitles}"</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("El profesor no ha hablado aún. Escribe en el campo o selecciona un botón para simular dictado.")
                
            if st.session_state.profesor_log:
                with st.expander("📝 Historial de Dictado de Clase (Subtítulos pasados)", expanded=True):
                    for log_item in st.session_state.profesor_log:
                        st.markdown(f"<p style='margin: 0; font-size: 0.88rem; color: #94a3b8;'>{log_item}</p>", unsafe_allow_html=True)
        
        render_subtitles_display()
                    
        if st.button("🧹 Limpiar historial y subtítulos", use_container_width=True):
            st.session_state.profesor_subtitles = ""
            st.session_state.profesor_log = []
            st.session_state.last_free_input = ""
            st.rerun()
            
        st.divider()
        
        # Lenguaje de Señas: Estudiante Mudo -> Profesor
        st.markdown("##### 2. Estudiante Mudo ➔ Profesor (Lenguaje de Señas con Visión)")
        
        # Alertas de señas dinámicas (Fragmento)
        @st.fragment(run_every=0.1)
        def render_alertas_señas():
            _, _, _, _, _, _, trans = cargar_estado_en_vivo()
            if trans:
                if "pregunta" in trans.lower() or "participar" in trans.lower():
                    bg_color = "rgba(99, 102, 241, 0.15)"
                    border_color = "#6366f1"
                    alert_title = "🙋 SOLICITUD DE PARTICIPACIÓN"
                    alert_msg = "Carlos López solicita la palabra para responder o preguntar."
                elif "ayuda" in trans.lower() or "soporte" in trans.lower() or "codigo" in trans.lower():
                    bg_color = "rgba(245, 158, 11, 0.15)"
                    border_color = "#f59e0b"
                    alert_title = "⚠️ SOLICITUD DE SOPORTE ACADÉMICO"
                    alert_msg = "Carlos López necesita ayuda del docente con el código."
                elif "termine" in trans.lower() or "ejercicio" in trans.lower() or "completado" in trans.lower() or "progreso" in trans.lower():
                    bg_color = "rgba(16, 185, 129, 0.15)"
                    border_color = "#10b981"
                    alert_title = "✅ META DE ACTIVIDAD ALCANZADA"
                    alert_msg = "Carlos López ha finalizado la actividad práctica asignada."
                else:
                    bg_color = "rgba(30, 41, 59, 0.7)"
                    border_color = "#334155"
                    alert_title = "🤟 SEÑA DETECTADA"
                    alert_msg = trans

                st.markdown(
                    f"""
                    <div style="background-color: {bg_color}; border: 2px solid {border_color}; padding: 16px; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px {border_color}22;">
                        <strong style="color: {border_color}; font-size: 0.85rem; font-weight: 800; letter-spacing: 1px;">{alert_title}</strong><br/>
                        <span style="color: #ffffff; font-size: 1.15rem; font-weight: 700; display: inline-block; margin-top: 5px;">"{trans}"</span><br/>
                        <p style="color: #94a3b8; font-size: 0.85rem; margin: 5px 0 0 0; font-weight: 600;">{alert_msg}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div style="background-color: #0b0f19; border: 1px solid #1e293b; padding: 20px; border-radius: 10px; text-align: center; color: #64748b;">
                        <span>Esperando traducción de señas... (Presiona la tecla <strong>'S'</strong> en la ventana de la cámara)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        render_alertas_señas()
            
    with col_inc_right:
        st.markdown("### 🎥 Feed de Cámara Web (Visión)")
        
        # Cámara en vivo dinámica (Fragmento)
        @st.fragment(run_every=0.1)
        def render_feed_camara():
            _, _, frame_path_cam, _, counts_cam, is_live_cam, _ = cargar_estado_en_vivo()
            if is_live_cam and frame_path_cam and os.path.exists(frame_path_cam):
                st.image(frame_path_cam, use_container_width=True)
                
                # Tarjetas de estado minimalistas
                st.markdown("##### Módulos de Visión Activos")
                o1, o2 = st.columns(2)
                with o1:
                    if counts_cam.get("sign_language", 0) > 0:
                        st.markdown("<div style='background-color: rgba(168, 85, 247, 0.15); border: 1px solid #a855f7; padding: 10px; border-radius: 8px; color: #c084fc; font-weight: 700; text-align: center; box-shadow: 0 0 10px rgba(168, 85, 247, 0.2);'>🤟 Lenguaje de Señas: ACTIVO</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0d0b21; border: 1px solid rgba(139, 92, 246, 0.2); padding: 10px; border-radius: 8px; color: #64748b; font-weight: 600; text-align: center;'>🤟 Lenguaje de Señas: Esperando</div>", unsafe_allow_html=True)
                with o2:
                    if counts_cam.get("person", 0) > 0:
                        st.markdown("<div style='background-color: rgba(6, 182, 212, 0.15); border: 1px solid #06b6d4; padding: 10px; border-radius: 8px; color: #22d3ee; font-weight: 700; text-align: center; box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);'>👤 Presencia: REGISTRADA</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);'>👤 Presencia: AUSENTE</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    """
                    <div style="background-color:#0d0b21; border: 1px dashed rgba(139, 92, 246, 0.3);
                                height: 280px; border-radius: 12px; display: flex;
                                justify-content: center; align-items: center; color: #94a3b8; margin-bottom: 15px;">
                        <span>Inicia vision/detection_yolo.py para conectar la cámara</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        render_feed_camara()

# ----------------- PESTAÑA ANALÍTICA DE ENGAGEMENT -----------------
with tab_engagement:
    # Pestaña de engagement dinámica (Fragmento)
    @st.fragment(run_every=0.1)
    def render_tab_engagement():
        estudiante_eng, aei_eng, frame_path_eng, _, counts_eng, is_live_eng, _ = cargar_estado_en_vivo()
        
        # Historial para gráficos
        if is_live_eng:
            seg_val = len(st.session_state.history) + 1
            st.session_state.history.append({
                "Segundo": seg_val,
                "Atención": estudiante_eng["atencion"],
                "Participación": estudiante_eng["participacion"],
                "AEI": aei_eng["score"]
            })
            if len(st.session_state.history) > 30:
                st.session_state.history.pop(0)
                
        COLORES = {"verde": "#06b6d4", "amarillo": "#a855f7", "rojo": "#ef4444"}
        color_eng = COLORES.get(aei_eng["estado"], "#4b5563")

        col_eng_left, col_eng_right = st.columns([1.8, 1.2])
        
        with col_eng_left:
            st.markdown(f"##### Estudiante: <span style='color: #ffffff; font-weight: 700;'>{estudiante_eng['nombre']}</span>", unsafe_allow_html=True)
            
            # AEI Score Card with Gradient and glowing styling
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #0d0b21 0%, #120e36 100%); border: 2px solid {color_eng}; border-radius: 16px; padding: 24px; text-align: center; box-shadow: 0 0 20px {color_eng}20; margin-bottom: 24px;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 3.8rem; font-weight: 800; text-shadow: 0 0 15px {color_eng}40;">{aei_eng['score']}</h1>
                    <p style="color: #c084fc; margin: 5px 0 0 0; font-size: 0.95rem; font-weight: 600; letter-spacing: 1px;">ACADEMIC ENGAGEMENT INDEX (AEI)</p>
                    <span style="color: {color_eng}; font-size: 0.9rem; font-weight: 700; border: 1px solid {color_eng}; padding: 3px 12px; border-radius: 20px; display: inline-block; margin-top: 10px; box-shadow: 0 0 8px {color_eng}30;">
                        ESTADO: {aei_eng['estado'].upper()}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Métricas individuales
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🏫 Asistencia", f"{estudiante_eng['asistencia']:.1f}%")
            m2.metric("🧠 Atención", f"{estudiante_eng['atencion']:.1f}%")
            m3.metric("🙋 Participación", f"{estudiante_eng['participacion']:.1f}%")
            m4.metric("📝 Actividades", f"{estudiante_eng['actividades']:.1f}%")
            
            st.divider()

            # Gráfico dinámico
            if is_live_eng and st.session_state.history:
                st.markdown("<p style='color: #94a3b8; font-weight: 600; margin-bottom: 10px;'>📈 Curva Dinámica de Engagement (Últimos 30s)</p>", unsafe_allow_html=True)
                df_hist = pd.DataFrame(st.session_state.history)
                st.line_chart(df_hist.set_index("Segundo"))
            else:
                st.info("El gráfico de curvas se activará al encender el script de la webcam o simulación manual.")

        with col_eng_right:
            st.markdown("##### 📱 Distracciones y Somnolencia (YOLO + MediaPipe)")
            
            # Streaming en vivo de la webcam visible en la pestaña de engagement
            if is_live_eng and frame_path_eng and os.path.exists(frame_path_eng):
                st.image(frame_path_eng, use_container_width=True)
            else:
                st.markdown(
                    """
                    <div style="background-color:#0d0b21; border: 1px dashed rgba(139, 92, 246, 0.3);
                                height: 200px; border-radius: 12px; display: flex;
                                justify-content: center; align-items: center; color: #94a3b8; margin-bottom: 15px;">
                        <span>Inicia vision/detection_yolo.py para conectar la cámara</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Tarjetas de alertas de distracción
            if is_live_eng:
                cell_active = counts_eng.get("cell phone", 0) > 0
                drowsy_active = counts_eng.get("drowsy", 0) > 0
                
                d1, d2 = st.columns(2)
                with d1:
                    if cell_active:
                        st.markdown("<div style='background-color: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);'>📱 Celular: DETECTADO</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0d0b21; border: 1px solid rgba(139, 92, 246, 0.2); padding: 10px; border-radius: 8px; color: #94a3b8; font-weight: 600; text-align: center;'>📱 Celular: Ninguno</div>", unsafe_allow_html=True)
                with d2:
                    if drowsy_active:
                        st.markdown("<div style='background-color: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center; box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);'>😴 Somnoliento: ALERTA</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0d0b21; border: 1px solid rgba(139, 92, 246, 0.2); padding: 10px; border-radius: 8px; color: #94a3b8; font-weight: 600; text-align: center;'>😴 Somnoliento: Normal</div>", unsafe_allow_html=True)
                        
                if cell_active:
                    st.markdown("<p style='color: #ef4444; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>📱 Estudiante distraído con el teléfono celular.</p>", unsafe_allow_html=True)
                elif drowsy_active:
                    st.markdown("<p style='color: #ef4444; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>😴 Fatiga severa registrada (Ojos cerrados / Somnolencia).</p>", unsafe_allow_html=True)
                elif counts_eng.get("person", 0) > 0:
                    st.markdown("<p style='color: #06b6d4; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>✨ Estudiante enfocado y libre de distracciones.</p>", unsafe_allow_html=True)
            else:
                st.info("Conecta la webcam para iniciar el monitoreo de distracciones.")
                
            st.divider()

            # Recomendaciones de Mentor IA
            st.markdown("##### 🤖 Análisis del Mentor IA")
            
            if "diagnostico_ia" not in st.session_state:
                st.session_state.diagnostico_ia = None

            if st.button("Analizar comportamiento con IA", use_container_width=True):
                datos_para_ia = {
                    "aei": aei_eng["score"],
                    "estado": aei_eng["estado"],
                    "asistencia": estudiante_eng["asistencia"],
                    "atencion": estudiante_eng["atencion"],
                    "participacion": estudiante_eng["participacion"],
                    "actividades": estudiante_eng["actividades"],
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

    render_tab_engagement()
