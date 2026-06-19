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
.stApp {
    background-color: #070a13;
    color: #e2e8f0;
}
[data-testid="stSidebar"] {
    background-color: #0b0f19 !important;
    border-right: 1px solid #1e293b;
}
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

st.sidebar.divider()
st.sidebar.title("🎛️ Simulación Manual (Pitch/Demo)")
modo_manual = st.sidebar.checkbox(
    "Forzar Modo Manual",
    value=False,
    help="Activa este control para manejar la demo usando los controles de la barra lateral sin depender de la cámara web activa."
)

if modo_manual:
    sim_presence = st.sidebar.selectbox("Asistencia (Estudiante)", ["Presente", "Ausente"])
    if sim_presence == "Presente":
        sim_distraction = st.sidebar.selectbox("Estado de Atención/Foco", ["Focalizado y Atento", "Distraído (Celular en mano)", "Fatigado (Somnoliento)"])
        sim_sign_ui = st.sidebar.selectbox("Lenguaje de Señas (Simulado)", [
            "Ninguno", 
            "Solicitud de Participación (Tengo una pregunta)", 
            "Solicitud de Soporte / Ayuda (Necesito ayuda con el código)", 
            "Actividad Terminada (Terminé el ejercicio)"
        ])
    else:
        sim_distraction = "Ausente"
        sim_sign_ui = "Ninguno"

st.sidebar.divider()
st.sidebar.markdown("""
### 💡 Guía para el Pitch de Inclusión:
1. **Modo Cámara**: Enciende la webcam (`detection_yolo.py`) y usa `S` para cambiar la seña del estudiante.
2. **Modo Manual**: Activa 'Forzar Modo Manual' arriba para simular la demo sin cámara.
3. **Profesor STT**: Selecciona frases típicas del profesor para ver los subtítulos adaptados.
""")

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

# Calcular simulación manual si modo_manual está activo
if modo_manual:
    asistencia_val = 100.0 if sim_presence == "Presente" else 0.0
    
    atencion_val = 100.0
    if sim_presence == "Ausente":
        atencion_val = 0.0
    elif sim_distraction == "Distraído (Celular en mano)":
        atencion_val = 20.0
    elif sim_distraction == "Fatigado (Somnoliento)":
        atencion_val = 10.0
        
    participacion_val = 70.0
    if sim_presence == "Ausente":
        participacion_val = 0.0
    else:
        if "Participación" in sim_sign_ui:
            participacion_val = 100.0
        elif "Soporte" in sim_sign_ui:
            participacion_val = 90.0
        elif "Terminada" in sim_sign_ui:
            participacion_val = 95.0
            
    actividades_val = 90.0 if sim_presence == "Presente" else 0.0
    
    aei_res = calcular_aei(asistencia_val, atencion_val, participacion_val, actividades_val)
    
    sim_counts = {
        "person": 1 if sim_presence == "Presente" else 0,
        "cell phone": 1 if (sim_presence == "Presente" and sim_distraction == "Distraído (Celular en mano)") else 0,
        "laptop": 1 if sim_presence == "Presente" else 0,
        "hand_raised": 0,
        "drowsy": 1 if (sim_presence == "Presente" and sim_distraction == "Fatigado (Somnoliento)") else 0,
        "sign_language": 1 if (sim_presence == "Presente" and sim_sign_ui != "Ninguno") else 0
    }
    
    if sim_sign_ui == "Ninguno":
        sim_transcript = ""
    elif "Participación" in sim_sign_ui:
        sim_transcript = "Tengo una pregunta / Solicito participar"
    elif "Soporte" in sim_sign_ui:
        sim_transcript = "Necesito ayuda con el codigo / Soporte"
    else:
        sim_transcript = "Termine el ejercicio / Avance completado"
        
    st.session_state.live_estudiante = {
        "nombre": "Carlos López",
        "asistencia": asistencia_val,
        "atencion": atencion_val,
        "participacion": participacion_val,
        "actividades": actividades_val,
    }
    st.session_state.live_aei = aei_res
    st.session_state.live_counts = sim_counts
    st.session_state.live_transcript = sim_transcript
    st.session_state.live_is_live = True
    st.session_state.live_frame_path = str(LIVE_STATE_PATH.parent / "live_frame.jpg")
    
    # Escritura del live_state.json para sincronizar otros módulos en modo manual
    state_mock = {
        "student_id": "carlos_lopez",
        "nombre": "Carlos López",
        "timestamp": str(time.strftime("%Y-%m-%dT%H:%M:%S-05:00")),
        "frame_path": st.session_state.live_frame_path or "",
        "detections": [
            {"label": "person", "confidence": 0.99, "bbox": [0.1, 0.1, 0.5, 0.8]}
        ] if sim_presence == "Presente" else [],
        "counts": sim_counts,
        "metrics": {
            "asistencia": asistencia_val,
            "atencion": atencion_val,
            "participacion": participacion_val,
            "actividades": actividades_val
        },
        "aei": aei_res,
        "transcript": sim_transcript
    }
    
    if sim_counts["cell phone"] > 0:
        state_mock["detections"].append({"label": "cell phone", "confidence": 0.92, "bbox": [0.6, 0.3, 0.15, 0.2]})
    if sim_counts["drowsy"] > 0:
        state_mock["detections"].append({"label": "drowsy", "confidence": 0.88, "bbox": [0.2, 0.2, 0.3, 0.4]})
    if sim_counts["sign_language"] > 0:
        state_mock["detections"].append({"label": "sign_language", "confidence": 0.95, "bbox": [0.4, 0.4, 0.2, 0.3]})
        
    try:
        temp_state_path = LIVE_STATE_PATH.with_suffix(".json.tmp")
        with open(temp_state_path, "w") as f:
            json.dump(state_mock, f, indent=2)
        os.replace(temp_state_path, LIVE_STATE_PATH)
    except Exception:
        pass

def cargar_estado_en_vivo():
    if modo_manual:
        return (
            st.session_state.live_estudiante,
            st.session_state.live_aei,
            st.session_state.live_frame_path,
            st.session_state.get("live_detections", []),
            st.session_state.live_counts,
            True,
            st.session_state.live_transcript
        )
    
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
    # Curva suave y realista de engagement inicial para que empiece viéndose excelente
    st.session_state.history = [
        {"Segundo": i, "Atención": 85.0 + (i % 3) * 4, "Participación": 65.0 + (i % 2) * 8, "AEI": 75.0 + (i % 4) * 3}
        for i in range(1, 15)
    ]

# --- UI Principal ---
st.title("🌈 Campus Guardian Access AI")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem; margin-top: -10px;'>Plataforma Inteligente de Inclusión y Alerta Temprana Académica</p>", unsafe_allow_html=True)

# Barra de estado dinámica (Fragmento)
@st.fragment(run_every=1.0)
def render_status_bar():
    _, _, _, _, _, is_live_dynamic, _ = cargar_estado_en_vivo()
    if is_live_dynamic:
        if modo_manual:
            st.success("🟢 Modo de Simulación Manual (Demo) Activo: Controlado desde la Barra Lateral")
        else:
            st.success("🟢 Conexión en vivo activa: Recibiendo datos de la webcam")
    else:
        st.warning("⚠️ Modo offline: Iniciando con datos estáticos (Corre vision/detection_yolo.py o activa Forzar Modo Manual)")

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
        @st.fragment(run_every=1.0)
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
        @st.fragment(run_every=1.0)
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
                        <span>Esperando traducción de señas... (Presiona la tecla <strong>'S'</strong> en la cámara o usa la simulación manual en la barra lateral)</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        render_alertas_señas()
            
    with col_inc_right:
        st.markdown("### 🎥 Feed de Cámara Web (Visión)")
        
        # Cámara en vivo dinámica (Fragmento)
        @st.fragment(run_every=1.0)
        def render_feed_camara():
            _, _, frame_path_cam, _, counts_cam, is_live_cam, _ = cargar_estado_en_vivo()
            if is_live_cam and frame_path_cam and os.path.exists(frame_path_cam):
                st.image(frame_path_cam, use_container_width=True)
                
                # Tarjetas de estado minimalistas
                st.markdown("##### Módulos de Visión Activos")
                o1, o2 = st.columns(2)
                with o1:
                    if counts_cam.get("sign_language", 0) > 0:
                        st.markdown("<div style='background-color: #6366f120; border: 1px solid #6366f1; padding: 10px; border-radius: 8px; color: #818cf8; font-weight: 700; text-align: center;'>🤟 Lenguaje de Señas: ACTIVO</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #64748b; font-weight: 600; text-align: center;'>🤟 Lenguaje de Señas: Esperando</div>", unsafe_allow_html=True)
                with o2:
                    if counts_cam.get("person", 0) > 0:
                        st.markdown("<div style='background-color: #10b98120; border: 1px solid #10b981; padding: 10px; border-radius: 8px; color: #10b981; font-weight: 700; text-align: center;'>👤 Presencia: REGISTRADA</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #ef444420; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center;'>👤 Presencia: AUSENTE</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    """
                    <div style="background-color:#0b0f19; border: 1px dashed #1e293b;
                                height: 280px; border-radius: 12px; display: flex;
                                justify-content: center; align-items: center; color: #64748b;">
                        <span>Inicia vision/detection_yolo.py para conectar la cámara</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        render_feed_camara()

# ----------------- PESTAÑA ANALÍTICA DE ENGAGEMENT -----------------
with tab_engagement:
    # Pestaña de engagement dinámica (Fragmento)
    @st.fragment(run_every=1.0)
    def render_tab_engagement():
        estudiante_eng, aei_eng, _, _, counts_eng, is_live_eng, _ = cargar_estado_en_vivo()
        
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
                
        COLORES = {"verde": "#10b981", "amarillo": "#f59e0b", "rojo": "#ef4444"}
        color_eng = COLORES.get(aei_eng["estado"], "#4b5563")

        col_eng_left, col_eng_right = st.columns([1.8, 1.2])
        
        with col_eng_left:
            st.markdown(f"##### Estudiante: <span style='color: #ffffff; font-weight: 700;'>{estudiante_eng['nombre']}</span>", unsafe_allow_html=True)
            
            # AEI Score Card
            st.markdown(
                f"""
                <div style="background-color: #0b0f19; border: 2px solid {color_eng}; border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 0 20px {color_eng}15; margin-bottom: 24px;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 3.8rem; font-weight: 800;">{aei_eng['score']}</h1>
                    <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.95rem; font-weight: 600; letter-spacing: 1px;">ACADEMIC ENGAGEMENT INDEX (AEI)</p>
                    <span style="color: {color_eng}; font-size: 0.9rem; font-weight: 700; border: 1px solid {color_eng}; padding: 3px 12px; border-radius: 20px; display: inline-block; margin-top: 10px;">
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
            
            # Tarjetas de alertas de distracción
            if is_live_eng:
                cell_active = counts_eng.get("cell phone", 0) > 0
                drowsy_active = counts_eng.get("drowsy", 0) > 0
                
                d1, d2 = st.columns(2)
                with d1:
                    if cell_active:
                        st.markdown("<div style='background-color: #ef444420; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center;'>📱 Celular: DETECTADO</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #94a3b8; font-weight: 600; text-align: center;'>📱 Celular: Ninguno</div>", unsafe_allow_html=True)
                with d2:
                    if drowsy_active:
                        st.markdown("<div style='background-color: #ef444420; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; color: #ef4444; font-weight: 700; text-align: center;'>😴 Somnoliento: ALERTA</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='background-color: #0b0f19; border: 1px solid #1e293b; padding: 10px; border-radius: 8px; color: #94a3b8; font-weight: 600; text-align: center;'>😴 Somnoliento: Normal</div>", unsafe_allow_html=True)
                        
                if cell_active:
                    st.markdown("<p style='color: #ef4444; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>📱 Estudiante distraído con el teléfono celular.</p>", unsafe_allow_html=True)
                elif drowsy_active:
                    st.markdown("<p style='color: #ef4444; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>😴 Fatiga severa registrada (Ojos cerrados / Somnolencia).</p>", unsafe_allow_html=True)
                elif counts_eng.get("person", 0) > 0:
                    st.markdown("<p style='color: #10b981; font-size: 0.85rem; margin-top: 10px; font-weight: 600;'>✨ Estudiante enfocado y libre de distracciones.</p>", unsafe_allow_html=True)
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
