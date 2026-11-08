import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from domain import (
    EstadoSolicitud,
    Estudiante,
    PersistenciaError,
    PrioridadSolicitud,
    Responsable,
    Solicitud,
    TipoSolicitud,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. CONTRATO DE PERSISTENCIA (Inversión de Dependencias - DIP)
# ==============================================================================
class SolicitudRepositoryProtocol(Protocol):
    """
    Define las operaciones estándar que cualquier repositorio de datos debe implementar.
    La lógica de negocio dependerá de este contrato, no de una base de datos específica.
    """
    def guardar(self, solicitud: Solicitud) -> Solicitud:
        ...

    def obtener_por_id(self, solicitud_id: int) -> Optional[Solicitud]:
        ...

    def listar_todas(self) -> List[Solicitud]:
        ...

    def siguiente_id(self) -> int:
        ...


# ==============================================================================
# 2. IMPLEMENTACIÓN CONCRETA (Repositorio JSON)
# ==============================================================================
class JsonSolicitudRepository:
    """
    Implementación concreta de almacenamiento en archivo JSON.
    Centraliza de forma segura todas las operaciones de I/O.
    """
    def __init__(self, ruta_archivo: Path) -> None:
        self._ruta = ruta_archivo

    def guardar(self, solicitud: Solicitud) -> Solicitud:
        solicitudes = self.listar_todas()
        actualizada = False
        
        for idx, existente in enumerate(solicitudes):
            if existente.id == solicitud.id:
                solicitudes[idx] = solicitud
                actualizada = True
                break
                
        if not actualizada:
            solicitudes.append(solicitud)

        self._escribir_archivo(solicitudes)
        return solicitud

    def obtener_por_id(self, solicitud_id: int) -> Optional[Solicitud]:
        for solicitud in self.listar_todas():
            if solicitud.id == solicitud_id:
                return solicitud
        return None

    def listar_todas(self) -> List[Solicitud]:
        if not self._ruta.exists():
            return []
            
        try:
            contenido = self._ruta.read_text(encoding="utf-8")
            if not contenido.strip():
                return []
            datos_crudos: List[Dict[str, Any]] = json.loads(contenido)
            return [self._deserializar(item) for item in datos_crudos]
        except json.JSONDecodeError as exc:
            logger.error("Archivo JSON corrupto en %s: %s", self._ruta, exc)
            raise PersistenciaError(f"Formato JSON inválido en {self._ruta}") from exc
        except OSError as exc:
            logger.error("Error de lectura en disco para %s: %s", self._ruta, exc)
            raise PersistenciaError(f"No se pudo leer el archivo {self._ruta}") from exc

    def siguiente_id(self) -> int:
        solicitudes = self.listar_todas()
        if not solicitudes:
            return 1
        return max(s.id for s in solicitudes) + 1

    def _escribir_archivo(self, solicitudes: List[Solicitud]) -> None:
        try:
            datos = [self._serializar(s) for s in solicitudes]
            self._ruta.write_text(
                json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Fallo de escritura en %s: %s", self._ruta, exc)
            raise PersistenciaError(f"Error al escribir en {self._ruta}") from exc

    # ==========================================================================
    # MÉTODOS DE MAPEO (ORM Manual: Diccionario <-> Objeto de Dominio)
    # ==========================================================================
    @staticmethod
    def _serializar(solicitud: Solicitud) -> Dict[str, Any]:
        return {
            "id": solicitud.id,
            "estudiante": {
                "dni": solicitud.estudiante.dni,
                "nombre": solicitud.estudiante.nombre,
                "legajo": solicitud.estudiante.legajo,
                "email": solicitud.estudiante.email,
            },
            "tipo": solicitud.tipo.value,
            "prioridad": solicitud.prioridad.value,
            "descripcion": solicitud.descripcion,
            "estado": solicitud.estado.value,
            "responsable": {
                "nombre": solicitud.responsable.nombre,
                "area": solicitud.responsable.area,
            }
            if solicitud.responsable else None,
            "fecha_creacion": solicitud.fecha_creacion,
        }

    @staticmethod
    def _deserializar(data: Dict[str, Any]) -> Solicitud:
        est_data = data["estudiante"]
        resp_data = data.get("responsable")
        
        return Solicitud(
            id=int(data["id"]),
            estudiante=Estudiante(
                dni=est_data["dni"],
                nombre=est_data["nombre"],
                legajo=est_data["legajo"],
                email=est_data["email"],
            ),
            tipo=TipoSolicitud(data["tipo"]),
            prioridad=PrioridadSolicitud(data["prioridad"]),
            descripcion=data["descripcion"],
            estado=EstadoSolicitud(data["estado"]),
            responsable=Responsable(
                nombre=resp_data["nombre"], area=resp_data["area"]
            ) if resp_data else None,
            fecha_creacion=data["fecha_creacion"],
        )