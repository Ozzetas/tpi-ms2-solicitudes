import logging
from dataclasses import dataclass
from typing import Dict, List

from domain import (
    CrearSolicitudDTO,
    EntidadNoEncontradaError,
    EstadoSolicitud,
    FiltroSolicitudDTO,
    PrioridadSolicitud,
    Responsable,
    Solicitud,
)
from repositories import SolicitudRepositoryProtocol

logger = logging.getLogger(__name__)


# ==============================================================================
# DATA TRANSFER OBJECTS DE SALIDA
# ==============================================================================
@dataclass(frozen=True)
class ReporteSolicitudesDTO:
    total: int
    por_estado: Dict[str, int]
    prioridad_alta: int


# ==============================================================================
# SERVICIO 1: GESTIÓN TRANSACCIONAL DE SOLICITUDES
# ==============================================================================
class GestorSolicitudesService:
    """
    Coordina exclusivamente las operaciones que mutan el estado o registran datos.
    Recibe el repositorio inyectado por constructor (DIP).
    """
    def __init__(self, repository: SolicitudRepositoryProtocol) -> None:
        self._repo = repository

    def registrar_solicitud(self, dto: CrearSolicitudDTO) -> Solicitud:
        nuevo_id = self._repo.siguiente_id()
        solicitud = Solicitud(
            id=nuevo_id,
            estudiante=dto.estudiante,
            tipo=dto.tipo,
            prioridad=dto.prioridad,
            descripcion=dto.descripcion,
        )
        guardada = self._repo.guardar(solicitud)
        logger.info("Solicitud #%d registrada para legajo %s", guardada.id, dto.estudiante.legajo)
        return guardada

    def asignar_responsable(self, solicitud_id: int, responsable: Responsable) -> Solicitud:
        solicitud = self._obtener_solicitud_existente(solicitud_id)
        # La regla de negocio se ejecuta en la entidad, no en el servicio (Move Method)
        solicitud.asignar_responsable(responsable)
        return self._repo.guardar(solicitud)

    def cambiar_estado(self, solicitud_id: int, nuevo_estado: EstadoSolicitud) -> Solicitud:
        solicitud = self._obtener_solicitud_existente(solicitud_id)
        solicitud.cambiar_estado(nuevo_estado)
        return self._repo.guardar(solicitud)

    def buscar_solicitudes(self, filtro: FiltroSolicitudDTO) -> List[Solicitud]:
        todas = self._repo.listar_todas()
        return [s for s in todas if self._cumple_filtro(s, filtro)]

    def _obtener_solicitud_existente(self, solicitud_id: int) -> Solicitud:
        """Centraliza la validación de existencia de la entidad (Extract Method)."""
        solicitud = self._repo.obtener_por_id(solicitud_id)
        if solicitud is None:
            raise EntidadNoEncontradaError(f"No existe la solicitud con ID {solicitud_id}.")
        return solicitud

    @staticmethod
    def _cumple_filtro(solicitud: Solicitud, filtro: FiltroSolicitudDTO) -> bool:
        """Aisla la lógica booleana de filtrado multicriterio."""
        if filtro.estado is not None and solicitud.estado != filtro.estado:
            return False
        if filtro.prioridad is not None and solicitud.prioridad != filtro.prioridad:
            return False
        if filtro.area_responsable is not None:
            if (
                solicitud.responsable is None
                or solicitud.responsable.area != filtro.area_responsable
            ):
                return False
        return True


# ==============================================================================
# SERVICIO 2: ANÁLISIS Y REPORTES
# ==============================================================================
class GeneradorReportesService:
    """
    Servicio dedicado exclusivamente a consolidación de métricas.
    Separa las lecturas analíticas de las escrituras transaccionales (SRP).
    """
    def __init__(self, repository: SolicitudRepositoryProtocol) -> None:
        self._repo = repository

    def generar_resumen(self) -> ReporteSolicitudesDTO:
        solicitudes = self._repo.listar_todas()
        
        conteo_estados: Dict[str, int] = {estado.value: 0 for estado in EstadoSolicitud}
        prioridad_alta = 0

        for solicitud in solicitudes:
            conteo_estados[solicitud.estado.value] += 1
            if solicitud.prioridad == PrioridadSolicitud.ALTA:
                prioridad_alta += 1

        return ReporteSolicitudesDTO(
            total=len(solicitudes),
            por_estado=conteo_estados,
            prioridad_alta=prioridad_alta,
        )