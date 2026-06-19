# Campus Guardian Access AI 🌈
### *Rompiendo barreras de comunicación y previniendo la deserción en tiempo real*

---

## 📌 1. El Problema: Las Aulas Tradicionales son Excluyentes
Hoy en día, las instituciones educativas enfrentan dos problemas críticos que ocurren en paralelo dentro del salón de clases:
1. **La Barrera del Silencio (Exclusión)**: Los estudiantes con discapacidad auditiva o del habla se encuentran en desventaja. Carecen de un canal fluido para interactuar con el docente. Si el profesor explica mirando al tablero, el estudiante sordo no puede leer sus labios; si el estudiante mudo tiene una duda de programación, no puede levantar la mano y expresar su frustración rápidamente sin interrumpir el ritmo general de la clase.
2. **La Deserción Invisible**: Los alumnos se desconectan. La somnolencia (fatiga crónica) y la distracción digital con teléfonos celulares son precursores directos del bajo rendimiento y la deserción escolar. Para cuando un docente nota estas fallas en las calificaciones, suele ser demasiado tarde.

---

## 💡 2. La Solución: Campus Guardian Access AI
Una plataforma inteligente de **Inclusión Bidireccional** y **Alerta Temprana** basada en Inteligencia Artificial y Visión Computacional. Transforma cualquier webcam común en un puente de accesibilidad y un sensor de engagement académico.

```
       [Profesor Habla]   ===>  (Subtítulos en Pantalla)  ===>   [Estudiante Sordo]
                                                                        ||
      [Docente Alerta]   <===  (Traducción de Señas AI)  <===   [Estudiante Mudo]
```

### Propuesta de Valor Única:
* **Accesibilidad Bidireccional Real**: Subtitulado instantáneo de lo que dice el profesor y alertas visuales automáticas cuando el estudiante utiliza lenguaje de señas para interactuar.
* **Índice de Engagement Académico (AEI)**: Un indicador compuesto en tiempo real que evalúa la Asistencia, la Atención y la Participación sin invadir la privacidad, alertando si un estudiante cae en zona de riesgo.
* **Recomendaciones Pedagógicas con IA**: Integración con Google Gemini para generar planes de acción inmediatos y personalizados para rescatar al estudiante antes de que falle la materia.

---

## ⚙️ 3. Características Clave del Producto

### A. Comunicación Bidireccional Activa (Inclusión)
* **Profesor a Estudiante Sordo**: Transcripción instantánea de la voz del docente. El estudiante sordo lee en su pantalla cada palabra explicada en tiempo real.
* **Estudiante Mudo a Profesor**: Detección inteligente de gestos y lenguaje de señas en el feed de la cámara. Al realizar una seña (como solicitar ayuda), la plataforma genera una alerta parpadeante en el panel del profesor:
  * 🙋 **Solicitud de Participación**: *"Tengo una pregunta / Quiero participar."*
  * ⚠️ **Solicitud de Soporte**: *"Necesito ayuda con el código / Error en consola."*
  * ✅ **Avance de Actividad**: *"Ejercicio terminado / Avance completado."*

### B. Módulo de Alerta Temprana (Prevención de Deserción)
* **Monitoreo No Invasivo**: YOLOv8 analiza el enfoque del alumno, detectando si está usando laptops (participación activa) o si se encuentra distraído con el teléfono celular.
* **Detección de Fatiga (MediaPipe)**: Monitoreo ocular continuo. Si el estudiante cierra los ojos prolongadamente (somnolencia), se genera una alerta inmediata.
* **Diagnóstico Pedagógico Automático**: Al presionar un botón, el Mentor de IA (Gemini) analiza el historial del alumno y ofrece al docente:
  1. *Diagnóstico preciso* del problema.
  2. *Acción inmediata* para el día de hoy.
  3. *Recomendación a mediano plazo* (tutorías, reubicación de puesto, dinámicas de grupo).

---

## 🚀 4. Guía para la Demo del Pitch (Paso a Paso)
*Para garantizar una presentación fluida ante el jurado, sigue este flujo usando la simulación manual o la cámara:*

1. **Mostrar el Estado Óptimo (Verde)**:
   * Coloca la asistencia en **Presente**, el foco en **Focalizado** y la seña en **Ninguno**.
   * *Mensaje de Venta*: "Aquí vemos a Carlos López, un estudiante en un estado de concentración ideal. Su índice AEI está sobre 90, lo que nos indica un alto compromiso."
2. **Simular el Dictado del Profesor (Subtítulos)**:
   * Haz clic en el botón `👋 Inicio de clase` en el panel de Streamlit.
   * *Mensaje de Venta*: "El profesor inicia su clase y de inmediato se generan subtítulos en pantalla. Si Carlos tuviera discapacidad auditiva, no se perdería ni un segundo de la explicación teórica."
3. **Simular Dificultad e Interacción Inclusiva (Señas - Naranja)**:
   * En los controles manuales de la barra lateral, cambia la Seña a `Solicitud de Soporte / Ayuda`.
   * *Mensaje de Venta*: "Supongamos que Carlos es mudo y se traba con un error de programación. Con solo hacer la seña de ayuda frente a su cámara web, el profesor recibe una alerta visual llamativa destacada en naranja: *Carlos necesita ayuda con el código*. No requiere gritar ni interrumpir, la inclusión ocurre de forma natural."
4. **Simular Pérdida de Foco (Rojo)**:
   * Cambia el Foco en la barra lateral a `Fatigado (Somnoliento)` o `Distraído (Celular en mano)`.
   * Verás cómo el indicador general AEI cae instantáneamente por debajo de 60 y el borde se ilumina en rojo. Las tarjetas de alerta muestran `Somnoliento: ALERTA`.
   * *Mensaje de Venta*: "Si el estudiante cae en un estado de fatiga o distracción recurrente, el índice de engagement AEI se desploma. El sistema detecta este riesgo académico de inmediato."
5. **Generar el Plan de Acción con IA (Gemini)**:
   * Haz clic en el botón `Analizar comportamiento con IA` en la esquina inferior derecha.
   * *Mensaje de Venta*: "No nos limitamos a reportar el problema. Nuestra IA generativa actúa como un tutor pedagógico adjunto, analizando las métricas y entregando al docente un diagnóstico clínico y un plan de acción: por ejemplo, reubicar a Carlos al frente o programar una tutoría par."

---

## 📈 5. Impacto y Viabilidad
* **Bajo Costo de Implementación**: Funciona sobre hardware existente (webcams estándar de laptops y procesadores domésticos Core i5), eliminando la necesidad de costosos sensores especializados.
* **Escalabilidad**: Arquitectura modular ligera y optimizada que procesa a 5 FPS para evitar la saturación de los servidores o computadores escolares.
* **Propósito Social**: Alineado con los Objetivos de Desarrollo Sostenible (ODS 4: Educación de Calidad y ODS 10: Reducción de Desigualdades).
