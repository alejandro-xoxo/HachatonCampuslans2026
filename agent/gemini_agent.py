import os
import hashlib
import json
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def _hash_datos(datos: dict) -> str:
    return hashlib.md5(json.dumps(datos, sort_keys=True).encode()).hexdigest()

_cache: dict = {}

def analizar_estudiante(datos: dict, api_key: str = None) -> dict:
    clave = _hash_datos(datos)
    if clave in _cache:
        return _cache[clave]

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "La variable de entorno GEMINI_API_KEY no está definida "
            "ni se ingresó una clave en la barra lateral del Dashboard."
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    prompt = f"""
Eres un tutor educativo experto. Analiza el siguiente reporte de un estudiante y responde EXACTAMENTE en este formato:

Diagnóstico: <descripción breve del estado actual del estudiante>
Acción: <acción inmediata que debe tomar el tutor o el estudiante>
Recomendación: <estrategia a mediano plazo para mejorar>

Datos del estudiante:
- AEI (score general): {datos['aei']} — Estado: {datos['estado']}
- Asistencia: {datos['asistencia']}/100
- Atención: {datos['atencion']}/100
- Participación: {datos['participacion']}/100
- Actividades entregadas: {datos['actividades']}/100

Responde únicamente con el formato indicado, sin texto adicional.
"""

    response = model.generate_content(prompt)
    texto = response.text.strip()

    resultado = {}
    for linea in texto.splitlines():
        if linea.startswith("Diagnóstico:"):
            resultado["diagnostico"] = linea.replace("Diagnóstico:", "").strip()
        elif linea.startswith("Acción:"):
            resultado["accion"] = linea.replace("Acción:", "").strip()
        elif linea.startswith("Recomendación:"):
            resultado["recomendacion"] = linea.replace("Recomendación:", "").strip()

    _cache[clave] = resultado
    return resultado
