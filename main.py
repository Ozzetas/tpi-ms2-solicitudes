import logging
from pathlib import Path

from domain import (
    CrearSolicitudDTO,
    EstadoSolicitud,
    Estudiante,
    FiltroSolicitudDTO,
    PrioridadSolicitud,
    Responsable,
    TipoSolicitud,
)
from repositories import JsonSolicitudRepository
from services import GeneradorReportesService, GestorSolicitudesService

# Configuración base del logger para la demostración
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def ejecutar_demostracion() -> None:
    # 1. Configurar almacenamiento aisaldo para la demostración
    ruta_db = Path("solicitudes_refactor_db.json")
    if ruta_db.exists():
        ruta_db.unlink()

    # 2. Inyección de dependencias
    repositorio = JsonSolicitudRepository(ruta_db)
    gestor = GestorSolicitudesService(repositorio)
    reportes = GeneradorReportesService(repositorio)

    # 3. Preparación de Objetos de Valor (Estudiantes)
    est_ana = Estudiante(
        dni="40111222",
        nombre="Ana Gomez",
        legajo="L-1001",
        email="ana@utn.edu.ar",
    )
    est_juan = Estudiante(
        dni="39222333",
        nombre="Juan Perez",
        legajo="L-1002",
        email="juan@utn.edu.ar",
    )

    # 4. Uso de los servicios transaccionales encapsulados
    s1 = gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=est_ana,
            tipo=TipoSolicitud.EQUIVALENCIA,
            prioridad=PrioridadSolicitud.ALTA,
            descripcion="Solicitud de equivalencia Matemática",
        )
    )
    
    gestor.registrar_solicitud(
        CrearSolicitudDTO(
            estudiante=est_juan,
            tipo=TipoSolicitud.CERTIFICADO,
            prioridad=PrioridadSolicitud.BAJA,
            descripcion="Certificado de alumno regular",
        )
    )

    responsable = Responsable(nombre="Carlos Ruiz", area="Secretaría Académica")
    gestor.asignar_responsable(s1.id, responsable)
    gestor.cambiar_estado(s1.id, EstadoSolicitud.RESUELTA)

    # 5. Consultas y reportes
    filtradas = gestor.buscar_solicitudes(
        FiltroSolicitudDTO(prioridad=PrioridadSolicitud.ALTA)
    )
    resumen = reportes.generar_resumen()

    print("\n--- RESULTADOS DEL REFACTORING ---")
    print(f"Solicitudes prioridad ALTA localizadas: {len(filtradas)}")
    print(f"Reporte general consolidado: {resumen}")


if __name__ == "__main__":
    ejecutar_demostracion()