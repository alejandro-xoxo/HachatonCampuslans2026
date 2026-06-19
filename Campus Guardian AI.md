# Campus Guardian AI

## Hackathon Campuslands 2026

### Reto

Las instituciones educativas generan constantemente información sobre asistencia, desempeño, participación y aprendizaje. Sin embargo, gran parte de estos datos no se utilizan para brindar acompañamiento personalizado ni para mejorar la experiencia educativa de forma proactiva.

El reto consiste en diseñar una solución basada en Inteligencia Artificial que ayude a mejorar:

* El aprendizaje.
* La participación estudiantil.
* La gestión académica.

La solución puede utilizar:

* Visión artificial.
* Agentes de IA.
* Analítica de datos.
* Asistentes inteligentes.
* Cualquier tecnología relevante.

---

# Idea Seleccionada

## Campus Guardian AI

Sistema de alerta temprana académica impulsado por Visión Artificial y Agentes de IA.

Su objetivo es identificar estudiantes en riesgo antes de que su rendimiento disminuya significativamente o abandonen su proceso de formación.

---

# Problema

Actualmente los instructores y mentores no siempre pueden detectar de forma temprana señales como:

* Baja asistencia.
* Falta de atención.
* Escasa participación.
* Distracciones frecuentes.
* Riesgo de deserción.

Normalmente estas señales se detectan cuando el problema ya es evidente.

---

# Solución

Campus Guardian AI analiza el comportamiento observado en el aula utilizando visión artificial y genera recomendaciones automáticas mediante agentes de IA.

El sistema:

1. Detecta estudiantes presentes.
2. Detecta posibles distracciones.
3. Detecta participación.
4. Calcula un score de riesgo.
5. Genera recomendaciones para mentores e instructores.

---

# Variables Analizadas

## Asistencia

Peso: 30%

Indicadores:

* Presente.
* Ausente.
* Retrasos.

---

## Atención Visual

Peso: 30%

Indicadores:

* Mirando al frente.
* Distracciones frecuentes.
* Uso de celular.

---

## Participación

Peso: 20%

Indicadores:

* Mano levantada.
* Interacción en clase.

---

## Actividad Académica

Peso: 20%

Indicadores simulados para MVP:

* Entregas realizadas.
* Actividades completadas.

---

# Sistema de Riesgo

## Verde

Score: 90 - 100

Estado:

* Buen rendimiento.
* Participación adecuada.

---

## Amarillo

Score: 60 - 89

Estado:

* Riesgo moderado.
* Requiere seguimiento.

---

## Rojo

Score: 0 - 59

Estado:

* Alto riesgo.
* Requiere intervención.

---

# Ejemplo

Estudiante: Miguel

Score: 42

Estado: ROJO

Motivos:

* Uso frecuente de celular.
* Baja participación.
* Ausencias detectadas.

Recomendación:

Programar mentoría individual y seguimiento académico.

---

# Pitch

Campus Guardian AI es un sistema de alerta temprana académica que utiliza visión artificial y agentes de IA para identificar señales de riesgo en estudiantes. Analiza asistencia, atención y participación en tiempo real, genera un score de riesgo y recomienda acciones concretas para instructores y mentores antes de que el estudiante reduzca su rendimiento o abandone su proceso de formación.

---

# Tecnologías

## Visión Artificial

* OpenCV
* YOLOv8

## Análisis y Datos

* FiftyOne

Repositorio:

https://github.com/voxel51/fiftyone

Uso dentro del proyecto:

* Visualización de detecciones.
* Exploración de datasets.
* Validación de resultados.
* Análisis de calidad de datos.

## Agente IA

* Gemini API

Funciones:

* Analizar score.
* Generar recomendaciones.
* Explicar riesgos.
* Proponer acciones.

## Dashboard

* Streamlit

Funciones:

* Mostrar métricas.
* Mostrar score.
* Mostrar estado.
* Mostrar recomendaciones.

---

# Arquitectura MVP

Webcam

↓

YOLOv8

↓

Detecciones

* Persona
* Celular
* Mano levantada

↓

Motor de Score

↓

Gemini

↓

Dashboard Streamlit

---

# Alcance Realista para 5 Horas

## Sí hacer

* Webcam funcionando.
* Detección de personas.
* Detección de celulares.
* Dashboard básico.
* Score automático.
* Recomendaciones con Gemini.
* Demo con FiftyOne.

## No hacer

* Entrenar modelos.
* Reconocimiento facial.
* Dataset propio grande.
* Backend complejo.
* Integraciones reales con Campuslands.

---

# Cronograma

## Hora 1

* Instalación.
* Configuración.
* Repositorio.
* Webcam.

## Hora 2

* YOLO.
* Detección de personas.
* Detección de celulares.

## Hora 3

* Dashboard Streamlit.
* Sistema de score.

## Hora 4

* Integración Gemini.
* Integración FiftyOne.

## Hora 5

* Pruebas.
* Correcciones.
* Preparación del pitch.

---

# División del Equipo

## Integrante 1

Visión Artificial

Responsabilidades:

* OpenCV.
* Webcam.
* YOLO.
* Detecciones.

---

## Integrante 2

Dashboard

Responsabilidades:

* Streamlit.
* Indicadores.
* Visualización.

---

## Integrante 3

Agente IA

Responsabilidades:

* Gemini.
* Prompts.
* Recomendaciones.

---

## Integrante 4

Datos

Responsabilidades:

* FiftyOne.
* Dataset.
* Validación.
* Métricas.

---

# Factor Diferenciador

La mayoría de equipos probablemente construirá:

* Chatbots.
* Tutores IA.
* Dashboards tradicionales.

Campus Guardian AI incorpora:

* Visión artificial.
* Detección en tiempo real.
* Sistema de alerta temprana.
* Agente IA para decisiones.
* FiftyOne para análisis visual.

Esto lo acerca más a una solución innovadora y demostrable en un hackathon de corta duración.

---

# Objetivo Final de la Demo

Mostrar cómo una cámara puede detectar señales tempranas de riesgo académico, convertirlas en métricas cuantificables y permitir que un agente de IA recomiende acciones concretas para mejorar el acompañamiento estudiantil.
