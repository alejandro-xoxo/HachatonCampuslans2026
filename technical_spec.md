# Especificación Técnica de Campus Guardian Access AI 🛠️
### *Arquitectura del Sistema, Librerías, Optimizaciones de CPU y Buenas Prácticas*

---

## 🏗️ 1. Arquitectura de Alto Nivel
El sistema está estructurado bajo un patrón de **Procesos Desacoplados de Productor-Consumidor**, comunicados mediante un contrato de datos unificado en formato JSON. Esta arquitectura evita el bloqueo mutuo y optimiza el uso de CPU.

```
+----------------------------------------+
| 🎥 Módulo de Visión (detection_yolo.py) |
|   - OpenCV webcam capture (640x480)    |
|   - YOLOv8 (Inferencia imgsz=320)      |
|   - MediaPipe (Detección de fatiga)    |
+----------------------------------------+
                   |
     Sobrescribe atómicamente a 5 FPS
                   v
        [ data/live_state.json ] <==== Contrato de datos unificado (schema.json)
        [ data/live_frame.jpg  ] <==== Frame en vivo en memoria secundaria
                   |
       +-----------+-----------+
       |                       |
       v                       v
 +-------------------------+ +-----------------------------------+
 | 📊 Dashboard (Streamlit) | | 💾 Pipeline FiftyOne              |
 |   - Recarga reactiva 1s  | |   - Carga histórico de imágenes   |
 |   - Demo override manual| |   - Limpieza automática >100 imgs |
 |   - Gemini 2.0 API /     | |   - Curation de datasets          |
 |     Fallback local       | +-----------------------------------+
 +-------------------------+
```

---

## 📦 2. Librerías y Tecnologías Principales
* **`ultralytics` (YOLOv8)**: Utilizado para la detección de personas, laptops y celulares. Usamos el modelo `yolov8n.pt` (Nano) por su mínima huella de cómputo.
* **`mediapipe`**: Proporciona el mapeo de landmarks faciales para medir la tasa de parpadeo y cierre prolongado de ojos (Drowsiness detector).
* **`streamlit`**: Framework reactivo para la interfaz web. Nos permite construir una interfaz de grado premium rápidamente en Python puro.
* **`google-generativeai`**: Cliente oficial SDK para interactuar con Gemini 2.0 (modelo `gemini-2.0-flash-lite`), que analiza métricas y formula diagnósticos de pedagogía activa.
* **`fiftyone`**: Herramienta de visualización de datos y control de calidad de modelos de visión. Se encarga de curar las muestras históricas almacenadas en disco.
* **`opencv-python`**: Captura de webcam, redimensionamiento, dibujado de rectángulos y textos, y manejo de la ventana GUI de control del presentador.

---

## ⚡ 3. Optimizaciones para CPU i5 (8.ª Gen) y 10GB RAM
Un cuello de botella típico en modelos de Deep Learning ejecutados localmente es la latencia de disco y la saturación de los hilos de CPU. Implementamos las siguientes mejoras clave:

1. **Limitación de Hilos en PyTorch (`torch.set_num_threads(4)`)**:
   Por defecto, PyTorch intenta usar todos los hilos del procesador, asfixiando a Streamlit y al sistema operativo. Al limitar los hilos de inferencia a 4, mantenemos el uso de CPU estable y evitamos retardos de rendering.
2. **Inferencia a Baja Resolución (`imgsz=320`)**:
   El feed de la cámara web se redimensiona a `640x480` píxeles, y la inferencia de YOLOv8 se ejecuta a `320x320` píxeles en lugar del estándar de `640x640`. Esto incrementa la velocidad de 1.5 FPS a más de 5-6 FPS en CPUs i5 antiguas.
3. **Reducción de E/S de Disco (Throttling)**:
   Guardar imágenes en disco a 30 FPS satura el almacenamiento y causa retrasos en Streamlit. Lo solucionamos dividiendo los frames en dos tipos:
   * **Frame en vivo (`live_frame.jpg`)**: Se sobrescribe el mismo archivo continuamente para el render del dashboard.
   * **Frames Históricos**: Solo se guarda un frame en la carpeta de base de datos cada 10 ciclos (1 en 10), liberando el 90% de las escrituras a disco.

---

## 🛠️ 4. Casos Prácticos de Buenas Prácticas de Programación

### Caso 1: Escritura Atómica de Archivos (Evitar Colisiones de Lectura/Escritura)
Cuando dos procesos independientes (el loop de OpenCV y el servidor de Streamlit) acceden al mismo archivo JSON (`live_state.json`), existe el riesgo de que Streamlit intente leer el archivo mientras OpenCV lo está escribiendo a medias, provocando un error fatal de lectura JSON.

**Cómo lo logramos (Implementación en `vision/detection_yolo.py`):**
```python
# 1. Escribimos los datos en un archivo temporal intermedio
temp_state_path = live_state_path.with_suffix(".json.tmp")
with open(temp_state_path, "w") as f:
    json.dump(state, f, indent=2)

# 2. Reemplazamos el archivo original usando una operación a nivel de SO (atómica y rápida)
os.replace(temp_state_path, live_state_path)
```
*Beneficio*: Streamlit siempre lee un JSON completo y bien formado. Cero caídas durante la demo.

---

### Caso 2: Gestión Autónoma de Memoria Secundaria (Prevención de Pérdida de Datos y Llenado de Disco)
Para evitar que el almacenamiento de imágenes de FiftyOne consuma todo el espacio de disco del ordenador escolar, implementamos una regla de limpieza automática FIFO (First In, First Out).

**Cómo lo logramos (Implementación en `fiftyone_app/fiftyone_pipeline.py`):**
El pipeline monitorea activamente la cantidad de samples almacenados. Si el total supera los 100 elementos, automáticamente elimina los registros más antiguos de la base de datos de FiftyOne y borra físicamente las imágenes `.jpg` del disco rígido, manteniendo la estabilidad térmica del procesador y la capacidad del disco.

---

### Caso 3: Resiliencia del Servicio (Fallback Offline ante Fallas de Conexión o API)
La plataforma no debe dejar de funcionar si no hay internet o si la API key de Google Gemini no se ingresa correctamente.

**Cómo lo logramos (Implementación en `dashboard/app_streamlit.py`):**
Creamos un motor de recomendación determinista local basado en reglas lógicas que mapea las métricas de Asistencia, Atención, Participación y Actividades. Si la llamada remota a Gemini falla o no tiene credenciales, el sistema ejecuta la función `generar_diagnostico_local` de manera invisible para el usuario.
*Beneficio*: Garantiza la continuidad total de la interfaz y la demo sin interrumpir la presentación al jurado.

---

### Caso 4: Modo de Simulación de Garantía (Garantía de Presentación Pitch)
Un hardware de webcam defectuoso, problemas de drivers o baja iluminación en la locación de la hackathon pueden arruinar la demostración de la visión artificial.

**Cómo lo logramos:**
Agregamos el **"Modo Manual (Pitch/Demo)"** en la barra lateral del Dashboard. Al activarlo, el sistema ignora las señales de la webcam en tiempo real y permite al presentador controlar los estados a mano con controles desplegables (Asistencia, Somnolencia, Celular, y Señas del lenguaje de señas) simulando los valores exactos requeridos.
*Beneficio*: Garantía del 100% de que la demo funcionará, pase lo que pase con los sensores físicos.

---

## 🏁 5. Instrucciones de Ejecución
Para arrancar el ecosistema completo en el computador objetivo:

```bash
# 1. Activar el Entorno Virtual
source ../.venv/bin/activate

# 2. Lanzar el Servidor del Dashboard (Streamlit)
streamlit run dashboard/app_streamlit.py --server.port 8501

# 3. En otra terminal: Iniciar el Bucle de Visión YOLOv8/Cámara Web
python vision/detection_yolo.py

# 4. (Opcional) Visualizar los datasets en FiftyOne
python fiftyone_app/fiftyone_pipeline.py
```
