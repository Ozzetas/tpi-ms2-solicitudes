from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ==============================================================================
# 1. JERARQUÍA DE EXCEPCIONES DE DOMINIO (Manejo explícito de errores)
# ==============================================================================
class SolicitudError(Exception):
    """Excepcion base para errores de reglas de negocio del dominio."""

class DatosInvalidosError(SolicitudError):
    """Se lanza cuando los datos de entrada de una entidad son invalidos."""

class EntidadNoEncontradaError(SolicitudError):
    """Se lanza cuando no se localiza una solicitud por su identificador."""

class TransicionEstadoInvalidaError(SolicitudError):
    """Se lanza cuando se intenta un cambio de estado prohibido por el flujo."""

class PersistenciaError(SolicitudError):
    """Se lanza ante fallos de lectura o escritura en el medio de almacenamiento."""


# ==============================================================================
# 2. ENUMERACIONES (Combatiendo los "Magic Numbers / Strings")
# ==============================================================================
class TipoSolicitud(str, Enum):
    EQUIVALENCIA = "EQUIVALENCIA"
    CERTIFICADO = "CERTIFICADO"
    MESA_ESPECIAL = "MESA_ESPECIAL"

class PrioridadSolicitud(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

class EstadoSolicitud(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_REVISION = "EN_REVISION"
    RESUELTA = "RESUELTA"
    CERRADA = "CERRADA"


# ==============================================================================
# 3. ENTIDADES Y OBJETOS DE VALOR (Tipado estricto e Inmutabilidad)
# ==============================================================================
@dataclass(frozen=True)
class Estudiante:
    dni: str
    nombre: str
    legajo: str
    email: str

    def __post_init__(self) -> None:
        # Validacion temprana (Fail-fast) para evitar propagar datos corruptos
        if not self.dni.strip() or not self.nombre.strip():
            raise DatosInvalidosError("El DNI y el nombre del estudiante son obligatorios.")
        if "@" not in self.email:
            raise DatosInvalidosError(f"El email '{self.email}' no tiene un formato valido.")

@dataclass(frozen=True)
class Responsable:
    nombre: str
    area: str

    def __post_init__(self) -> None:
        if not self.nombre.strip() or not self.area.strip():
            raise DatosInvalidosError("El nombre y el area del responsable son obligatorios.")


# ==============================================================================
# 4. OBJETOS DE TRANSFERENCIA DE DATOS (Combatiendo "Long Parameter List")
# ==============================================================================
@dataclass(frozen=True)
class CrearSolicitudDTO:
    """Introduce Parameter Object: encapsula los parametros de creacion."""
    estudiante: Estudiante
    tipo: TipoSolicitud
    prioridad: PrioridadSolicitud
    descripcion: str

    def __post_init__(self) -> None:
        if not self.descripcion.strip():
            raise DatosInvalidosError("La descripcion de la solicitud no puede estar vacia.")

@dataclass(frozen=True)
class FiltroSolicitudDTO:
    """Introduce Parameter Object: encapsula criterios de filtrado."""
    estado: Optional[EstadoSolicitud] = None
    prioridad: Optional[PrioridadSolicitud] = None
    area_responsable: Optional[str] = None


# ==============================================================================
# 5. ENTIDAD PRINCIPAL (Aplicación de "Move Method" para encapsular comportamiento)
# ==============================================================================
@dataclass
class Solicitud:
    id: int
    estudiante: Estudiante
    tipo: TipoSolicitud
    prioridad: PrioridadSolicitud
    descripcion: str
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE
    responsable: Optional[Responsable] = None
    fecha_creacion: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def asignar_responsable(self, nuevo_responsable: Responsable) -> None:
        """
        Move Method: La entidad es dueña de su estado. 
        Ella misma controla las reglas de negocio, no una función externa.
        """
        if self.estado == EstadoSolicitud.CERRADA:
            raise TransicionEstadoInvalidaError(
                f"No se puede reasignar la solicitud #{self.id} porque esta CERRADA."
            )
        self.responsable = nuevo_responsable
        if self.estado == EstadoSolicitud.PENDIENTE:
            self.estado = EstadoSolicitud.EN_REVISION

    def cambiar_estado(self, nuevo_estado: EstadoSolicitud) -> None:
        """Valida transiciones de estado directamente en el modelo."""
        if (
            self.estado == EstadoSolicitud.CERRADA
            and nuevo_estado != EstadoSolicitud.CERRADA
        ):
            raise TransicionEstadoInvalidaError(
                f"La solicitud #{self.id} se encuentra CERRADA y no admite reapertura."
            )
        if (
            nuevo_estado == EstadoSolicitud.RESUELTA
            and self.responsable is None
        ):
            raise TransicionEstadoInvalidaError(
                f"La solicitud #{self.id} requiere un responsable antes de marcarse RESUELTA."
            )
        self.estado = nuevo_estado