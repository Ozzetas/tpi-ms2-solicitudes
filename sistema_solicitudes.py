import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# 1. Configuración de logging estructurado (Prohibido silenciar errores con 'pass')
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Tipado estricto de variables globales y uso de Path para manejo seguro de I/O
ARCHIVO_DB: Path = Path("solicitudes_db.json")
solicitudes_memoria: List[Dict[str, Any]] = []


def procesar_sistema(
    accion: int,
    id_sol: Optional[int] = None,
    dni_est: Optional[str] = None,
    nombre_est: Optional[str] = None,
    legajo_est: Optional[str] = None,
    email_est: Optional[str] = None,
    tipo: Optional[int] = None,
    prioridad: Optional[int] = None,
    descripcion: Optional[str] = None,
    estado_nuevo: Optional[str] = None,
    responsable_nombre: Optional[str] = None,
    responsable_area: Optional[str] = None,
    filtro_estado: Optional[str] = None,
    filtro_prio: Optional[str] = None,
) -> Union[Dict[str, Any], bool, List[Dict[str, Any]], None]:
    
    global solicitudes_memoria

    # 3. Manejo explícito de excepciones de I/O y parseo de datos
    try:
        if ARCHIVO_DB.exists():
            contenido = ARCHIVO_DB.read_text(encoding="utf-8")
            solicitudes_memoria = json.loads(contenido) if contenido.strip() else []
    except json.JSONDecodeError as exc:
        logger.error("Archivo JSON corrupto. Se inicializará memoria vacía. Detalle: %s", exc)
        solicitudes_memoria = []
    except OSError as exc:
        logger.error("Fallo de lectura en disco al acceder a %s: %s", ARCHIVO_DB, exc)
        solicitudes_memoria = []

    # Operacion 1: Registrar una nueva solicitud academica
    if accion == 1:
        # Validación temprana de strings obligatorios
        if dni_est and nombre_est and descripcion:
            if tipo in [1, 2, 3] and prioridad in [1, 2, 3]:
                nuevo_id = len(solicitudes_memoria) + 1
                nueva: Dict[str, Any] = {
                    "id": nuevo_id,
                    "dni_est": dni_est,
                    "nombre_est": nombre_est,
                    "legajo_est": legajo_est,
                    "email_est": email_est,
                    "tipo": "EQUIVALENCIA" if tipo == 1 else ("CERTIFICADO" if tipo == 2 else "MESA_ESPECIAL"),
                    "prioridad": "ALTA" if prioridad == 1 else ("MEDIA" if prioridad == 2 else "BAJA"),
                    "descripcion": descripcion,
                    "estado": "PENDIENTE",
                    "responsable_nombre": "SIN_ASIGNAR",
                    "responsable_area": "NINGUNA",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                solicitudes_memoria.append(nueva)
                
                try:
                    ARCHIVO_DB.write_text(json.dumps(solicitudes_memoria, indent=2), encoding="utf-8")
                except OSError as exc:
                    logger.error("Fallo de escritura en disco al guardar nueva solicitud: %s", exc)
                    
                return nueva
        return None

    # Operacion 2: Cambiar el estado de una solicitud existente
    elif accion == 2:
        for s in solicitudes_memoria:
            if s["id"] == id_sol:
                if s["estado"] == "CERRADA" and estado_nuevo == "PENDIENTE":
                    return False
                
                # Asignación segura asumiendo que estado_nuevo nunca llega vacío si entra aquí
                s["estado"] = estado_nuevo if estado_nuevo else s["estado"]
                
                try:
                    ARCHIVO_DB.write_text(json.dumps(solicitudes_memoria, indent=2), encoding="utf-8")
                except OSError as exc:
                    logger.error("Fallo de escritura al actualizar estado: %s", exc)
                return True
        return False

    # Operacion 3: Asignar un responsable administrativo a la solicitud
    elif accion == 3:
        for s in solicitudes_memoria:
            if s["id"] == id_sol:
                s["responsable_nombre"] = responsable_nombre
                s["responsable_area"] = responsable_area
                if s["estado"] == "PENDIENTE":
                    s["estado"] = "EN_REVISION"
                    
                try:
                    ARCHIVO_DB.write_text(json.dumps(solicitudes_memoria, indent=2), encoding="utf-8")
                except OSError as exc:
                    logger.error("Fallo de escritura al asignar responsable: %s", exc)
                return True
        return False

    # Operacion 4: Buscar y filtrar solicitudes por estado o prioridad
    elif accion == 4:
        res: List[Dict[str, Any]] = []
        for s in solicitudes_memoria:
            cumple = True
            if filtro_estado is not None and s["estado"] != filtro_estado:
                cumple = False
            if filtro_prio is not None and s["prioridad"] != filtro_prio:
                cumple = False
            if cumple:
                res.append(s)
        return res

    # Operacion 5: Generar reporte estadistico basico
    elif accion == 5:
        total = len(solicitudes_memoria)
        pendientes = sum(1 for s in solicitudes_memoria if s.get("estado") == "PENDIENTE")
        en_rev = sum(1 for s in solicitudes_memoria if s.get("estado") == "EN_REVISION")
        resueltas = sum(1 for s in solicitudes_memoria if s.get("estado") == "RESUELTA")
        cerradas = sum(1 for s in solicitudes_memoria if s.get("estado") == "CERRADA")
        alta = sum(1 for s in solicitudes_memoria if s.get("prioridad") == "ALTA")
        
        reporte: Dict[str, int] = {
            "total": total,
            "pendientes": pendientes,
            "en_revision": en_rev,
            "resueltas": resueltas,
            "cerradas": cerradas,
            "prioridad_alta": alta,
        }
        return reporte

    return None


if __name__ == "__main__":
    # Limpio el archivo previo para ejecutar una prueba controlada desde cero
    if ARCHIVO_DB.exists():
        try:
            ARCHIVO_DB.unlink()
        except OSError as exc:
            logger.error("No se pudo limpiar la base de datos de prueba: %s", exc)

    # Demostracion funcional base con los parámetros correctamente tipados
    s1 = procesar_sistema(
        1, 
        dni_est="40111222", 
        nombre_est="Ana Gomez", 
        legajo_est="L-1001", 
        email_est="ana@utn.edu.ar", 
        tipo=1, 
        prioridad=1, 
        descripcion="Equivalencia"
    )
    
    procesar_sistema(3, id_sol=1, responsable_nombre="Carlos Ruiz", responsable_area="Academica")
    procesar_sistema(2, id_sol=1, estado_nuevo="RESUELTA")
    
    # Invocación de reporte manejada de forma segura para impresión
    resultado_reporte = procesar_sistema(5)
    print(resultado_reporte)