def calcular_aei(asistencia: float, atencion: float, participacion: float, actividades: float) -> dict:
    score = (asistencia * 0.20) + (atencion * 0.30) + (participacion * 0.30) + (actividades * 0.20)

    if score >= 90:
        estado = "verde"
    elif score >= 60:
        estado = "amarillo"
    else:
        estado = "rojo"

    return {"score": round(score, 2), "estado": estado}
