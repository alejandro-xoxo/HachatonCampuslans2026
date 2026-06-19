import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from analytics.aei_engine import calcular_aei
from agent.gemini_agent import analizar_estudiante

# --- Datos de prueba ---
estudiante = {
    "nombre": "Carlos López",
    "asistencia": 75,
    "atencion": 60,
    "participacion": 55,
    "actividades": 80,
}

# --- Cálculo AEI ---
aei = calcular_aei(
    estudiante["asistencia"],
    estudiante["atencion"],
    estudiante["participacion"],
    estudiante["actividades"],
)

COLORES = {"verde": "#2ecc71", "amarillo": "#f1c40f", "rojo": "#e74c3c"}
color = COLORES[aei["estado"]]

# --- UI ---
st.set_page_config(page_title="Dashboard AEI", layout="wide")
st.title("📊 Dashboard de Engagement Estudiantil")
st.markdown(f"**Estudiante:** {estudiante['nombre']}")
st.divider()

# Score AEI
st.markdown(
    f"""
    <div style="background-color:{color};padding:24px;border-radius:12px;text-align:center;">
        <h1 style="color:white;margin:0;">AEI: {aei['score']}</h1>
        <h3 style="color:white;margin:0;">Estado: {aei['estado'].upper()}</h3>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# Métricas individuales
st.subheader("Métricas Individuales")
col1, col2, col3, col4 = st.columns(4)
col1.metric("🏫 Asistencia", f"{estudiante['asistencia']}/100", help="Peso: 20%")
col2.metric("🧠 Atención", f"{estudiante['atencion']}/100", help="Peso: 30%")
col3.metric("🙋 Participación", f"{estudiante['participacion']}/100", help="Peso: 30%")
col4.metric("📝 Actividades", f"{estudiante['actividades']}/100", help="Peso: 20%")
st.divider()

# Recomendación Gemini
st.subheader("🤖 Análisis por IA (Gemini)")

if st.button("Generar diagnóstico"):
    with st.spinner("Consultando a Gemini..."):
        try:
            resultado = analizar_estudiante({
                "aei": aei["score"],
                "estado": aei["estado"],
                "asistencia": estudiante["asistencia"],
                "atencion": estudiante["atencion"],
                "participacion": estudiante["participacion"],
                "actividades": estudiante["actividades"],
            })
            st.success("✅ Diagnóstico generado")
            st.markdown(f"**Diagnóstico:** {resultado.get('diagnostico', 'N/A')}")
            st.markdown(f"**Acción:** {resultado.get('accion', 'N/A')}")
            st.markdown(f"**Recomendación:** {resultado.get('recomendacion', 'N/A')}")
        except EnvironmentError as e:
            st.error(str(e))
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):
                st.warning("⚠️ Cuota de Gemini agotada. Mostrando diagnóstico de respaldo.")
                st.markdown(f"**Diagnóstico:** El estudiante presenta un AEI de {aei['score']} con estado {aei['estado'].upper()}.")
                st.markdown("**Acción:** Revisar métricas con el tutor asignado.")
                st.markdown("**Recomendación:** Reforzar participación y atención en clase mediante actividades interactivas.")
            else:
                st.error(f"Error inesperado: {e}")
