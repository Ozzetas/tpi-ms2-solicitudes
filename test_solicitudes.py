import pytest
from pathlib import Path
from typing import Tuple

from domain import (
    CrearSolicitudDTO,
    DatosInvalidosError,
    EntidadNoEncontradaError,
    EstadoSolicitud,
    Estudiante,
    FiltroSolicitudDTO,
    PrioridadSolicitud,
    Responsable,
    TipoSolicitud,
    TransicionEstadoInvalidaError,
)
from repositories import JsonSolicitudRepository
from services import GeneradorReportesService, GestorSolicitudesService

# ==============================================================================
# FIXTURES (Inyección de dependencias y aislamiento de estado)
# ==============================================================================

# Suprimimos el chequeo estricto de Pylance exclusivamente en este decorador
# debido a la ausencia de type stubs nativos (.pyi) en la librería pytest.
@pytest.fixture  # type: ignore
def servicios(tmp_path: Path) -> Tuple[GestorSolicitudesService, GeneradorReportesService]:
    """
    Arrange: Prepara el entorno instanciando un repositorio efímero.
    Garantiza que la base de datos comience vacía en cada ejecución unitaria,
    cumpliendo con el principio de pruebas independientes.
    """
    archivo_temp: Path = tmp_path / "test_db.json"
    repo = JsonSolicitudRepository(archivo_temp)
    return GestorSolicitudesService(repo), GeneradorReportesService(repo)


@pytest.fixture  # type: ignore
def estudiante_valido() -> Estudiante:
    """Provee un Objeto de Valor inmutable para reutilizar (DRY)."""
    return Estudiante(
        dni="40111222",
        nombre="Ana Gomez",
        legajo="L-1001",
        email="ana@utn.edu.ar",
    )

# ==============================================================================
# SUITE DE VERIFICACIÓN QA AUTOMATION
# ==============================================================================

def test_registrar_solicitud_exitosamente(
    servicios: Tuple[GestorSolicitudesService, GeneradorReportesService], 
    estudiante_valido: Estudiante
) -> None:
    gestor, _ = servicios
    dto = CrearSolicitudDTO(
        estudiante=estudiante_valido,
        tipo=TipoSolicitud.EQUIVALENCIA,
        prioridad=PrioridadSolicitud.ALTA,
        descripcion="Equivalencia de Programacion I",
    )
    
    # Act
    creada = gestor.registrar_solicitud(dto)

    # Assert
    assert creada.id == 1
    assert creada.estado == EstadoSolicitud.PENDIENTE
    assert creada.estudiante.legajo == "L-1001"


def test_asignar_responsable_cambia_a_en_revision(
    servicios: Tuple[GestorSolicitudesService, GeneradorReportesService], 
    estudiante_valido: Estudiante
) -> None:
    gestor, _ = servicios
    creada = gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=estudiante_valido,
            tipo=TipoSolicitud.CERTIFICADO,
            prioridad=PrioridadSolicitud.MEDIA,
            descripcion="Certificado analitico",
        )
    )
    resp = Responsable(nombre="Laura Diaz", area="Alumnos")
    
    # Act
    actualizada = gestor.asignar_responsable(creada.id, resp)

    # Assert
    assert actualizada.estado == EstadoSolicitud.EN_REVISION
    assert actualizada.responsable == resp


def test_bloquea_resolucion_sin_responsable_asignado(
    servicios: Tuple[GestorSolicitudesService, GeneradorReportesService], 
    estudiante_valido: Estudiante
) -> None:
    gestor, _ = servicios
    creada = gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=estudiante_valido,
            tipo=TipoSolicitud.MESA_ESPECIAL,
            prioridad=PrioridadSolicitud.ALTA,
            descripcion="Mesa especial mayo",
        )
    )
    
    # type: ignore suprime el error de Pylance sobre la firma desconocida de pytest.raises
    with pytest.raises(TransicionEstadoInvalidaError):  # type: ignore
        gestor.cambiar_estado(creada.id, EstadoSolicitud.RESUELTA)


def test_filtrar_y_generar_reporte_conserva_comportamiento(
    servicios: Tuple[GestorSolicitudesService, GeneradorReportesService], 
    estudiante_valido: Estudiante
) -> None:
    gestor, reportes = servicios
    
    s1 = gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=estudiante_valido,
            tipo=TipoSolicitud.EQUIVALENCIA,
            prioridad=PrioridadSolicitud.ALTA,
            descripcion="Equivalencia 1",
        )
    )
    gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=estudiante_valido,
            tipo=TipoSolicitud.CERTIFICADO,
            prioridad=PrioridadSolicitud.BAJA,
            descripcion="Certificado 2",
        )
    )
    
    gestor.asignar_responsable(s1.id, Responsable("Carlos Ruiz", "Academica"))
    gestor.cambiar_estado(s1.id, EstadoSolicitud.RESUELTA)

    altas = gestor.buscar_solicitudes(FiltroSolicitudDTO(prioridad=PrioridadSolicitud.ALTA))
    resumen = reportes.generar_resumen()

    assert len(altas) == 1
    assert resumen.total == 2
    assert resumen.prioridad_alta == 1
    assert resumen.por_estado["RESUELTA"] == 1
    assert resumen.por_estado["PENDIENTE"] == 1


def test_validacion_datos_estudiante_invalidos() -> None:
    # Verificamos la validación fail-fast integrada en la entidad
    with pytest.raises(DatosInvalidosError):  # type: ignore
        Estudiante(dni="", nombre="   ", legajo="L-99", email="correo_invalido")


def test_error_solicitud_inexistente(
    servicios: Tuple[GestorSolicitudesService, GeneradorReportesService]
) -> None:
    gestor, _ = servicios
    with pytest.raises(EntidadNoEncontradaError):  # type: ignore
        gestor.cambiar_estado(999, EstadoSolicitud.CERRADA)