# Handoff — Campus Guardian Access AI
**Hackathon Campuslands 2026**

> Este documento es para que retomes este proyecto en una conversación nueva.
> Pégalo completo al inicio del chat junto con el mensaje: "Continúa ayudándome con este proyecto, este es el contexto completo."

---

## 1. Qué es el proyecto

Sistema de alerta temprana académica + accesibilidad para un hackathon. Usa visión artificial (YOLOv8 + OpenCV + MediaPipe) para detectar señales de riesgo en estudiantes (asistencia, atención, participación), calcula un score llamado **AEI (Academic Engagement Index)**, y un agente con **Gemini API** genera recomendaciones. Todo se visualiza en un **dashboard Streamlit**, y **FiftyOne** (voxel51) es la pieza central de análisis/visualización de datasets — es el diferenciador del proyecto frente al jurado.

La versión ampliada ("Access AI") agrega un módulo de inclusión: subtítulos en tiempo real (Speech-to-Text con Whisper) para estudiantes sordos, y detección de lenguaje de señas para estudiantes mudos.

Repo del proyecto: `https://github.com/alejandro-xoxo/HachatonCampuslans2026.git`

---

## 2. Stack tecnológico

- **Visión:** OpenCV, YOLOv8 (modelo `yolov8n.pt` pre-entrenado, sin fine-tuning), MediaPipe (Face Mesh para somnolencia)
- **Datos/análisis:** FiftyOne — datasets: Participación, Distracciones, Accesibilidad, Asistencia
- **Agente IA:** Gemini API (vía Google AI Studio, librería `google-generativeai`)
- **Dashboard:** Streamlit
- **Transcripción:** Whisper (pendiente de implementar)
- **Herramientas de desarrollo con IA:** Amazon Q (en VS Code) y Antigravity CLI (`agy`), usadas en paralelo sobre ramas Git distintas

---

## 3. Equipo y división de trabajo

| Persona | Responsabilidad | Rama Git | Estado |
|---|---|---|---|
| Miguel | Visión artificial + FiftyOne | `feature/vision-fiftyone` | Completó `detection_yolo.py` y `fiftyone_pipeline.py` (hasta su prompt 3) |
| Juan Pablo | Analítica + Agente Gemini + Dashboard | `feature/agent-dashboard` | Completó los 3 módulos: `aei_engine.py`, `gemini_agent.py`, `app_streamlit.py` |

Flujo de Git: ramas feature → merge a `dev` → merge final a `main` antes de la demo.

---

## 4. Estructura actual del repo

```
HachatonCampuslans2026/
├── data/
│   └── frames/                  # frames capturados por detection_yolo.py
├── fiftyone_app/
│   └── fiftyone_pipeline.py     # carga frames+detecciones a FiftyOne, dataset persistente
├── vision/
│   └── detection_yolo.py        # OpenCV + YOLOv8, detecta persona/celular/laptop
├── analytics/
│   └── aei_engine.py            # calcula AEI con pesos 20/30/30/20 (Juan Pablo)
├── agent/
│   └── gemini_agent.py          # llama a Gemini con throttling (Juan Pablo)
├── dashboard/
│   └── app_streamlit.py         # muestra AEI, estado, recomendación (Juan Pablo)
├── .gitignore
├── Campus Guardian AI.md        # documento de especificación del reto
├── requirements.txt
├── test_fiftyone.py
└── yolov8n.pt                   # modelo descargado — DEBERÍA estar en .gitignore, aún no se ha movido
```

---

## 5. Pipeline funcional (lo que ya corre end-to-end por separado)

```
Webcam → detection_yolo.py (YOLOv8+OpenCV)
       → guarda frames en data/frames/ + JSON de detecciones
       → fiftyone_pipeline.py carga eso a un fo.Dataset persistente
       → fo.launch_app() para visualización
```
```
analytics/aei_engine.py → calcula AEI y estado (verde/amarillo/rojo)
       → agent/gemini_agent.py recibe esos datos y genera diagnóstico/recomendación
       → dashboard/app_streamlit.py muestra todo
```

**Lo que falta integrar:** conectar la salida real de `fiftyone_pipeline.py`/`detection_yolo.py` con `aei_engine.py` mediante un contrato de datos común (`data/schema.json`, aún no creado formalmente). Actualmente cada mitad del pipeline corre con datos de prueba por separado.

---

## 6. Problemas ya resueltos (no repetir)

1. **Gemini API se agotaba en segundos** → la causa era llamar a la API en cada frame del loop de video sin control de frecuencia. Se resolvió con throttling (llamar cada 10-15s o solo cuando el AEI cambia de categoría).
2. **Confusión sobre "subir datos" a FiftyOne** → se aclaró: es cargar imágenes+detecciones como `Sample` dentro de un `Dataset` local con `persistent=True`, no subir nada a internet.
3. **Dependencia faltante en `requirements.txt`** → causaba error de ejecución. Ya identificada y corregida (no se especificó cuál exactamente, revisar el diff del commit si hace falta).
4. **Confusión Antigravity vs VS Code** → se aclaró que Antigravity no es extensión de VS Code; es app/CLI separada que se abre directamente sobre la carpeta del repo clonado, detectando la rama Git activa automáticamente.

---

## 7. Pendientes inmediatos

1. Mover `yolov8n.pt` a `.gitignore` (es un binario de modelo, no debería versionarse).
2. Crear formalmente `data/schema.json` como contrato entre el módulo de visión y el de analítica.
3. Mergear `feature/vision-fiftyone` y `feature/agent-dashboard` hacia `dev`.
4. Prueba end-to-end completa: webcam → FiftyOne → AEI → Gemini → Streamlit.
5. Módulos del documento aún no implementados: Speech-to-Text (Whisper) para subtítulos, detección de lenguaje de señas, detección de somnolencia (MediaPipe), módulo de permanencia en clase (entrada/salida del aula), datasets de Accesibilidad y Asistencia en FiftyOne (hoy solo existe el de Distracciones/Participación).
6. Preparar pitch final con demo en vivo de FiftyOne abierto en una pestaña separada durante toda la presentación.

---

## 8. Cómo seguir trabajando

- Usar Amazon Q para ediciones rápidas en VS Code.
- Usar Antigravity CLI (`agy`) parado en la rama correspondiente del repo clonado para construir módulos nuevos completos (usar Plan Mode para tareas complejas).
- Cada prompt debe enfocarse en **un solo módulo/responsabilidad**, probarlo, y luego seguir con el siguiente — no pedir "todo el sistema" de una vez.