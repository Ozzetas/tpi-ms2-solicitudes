# Sistema Modular de Gestión de Solicitudes Académicas

Desarrollo y refactorización orientada a objetos de un sistema de gestión académica, enfocado en **Clean Architecture**, principios **SOLID** y automatización de pruebas QA. Proyecto integrador correspondiente a la cátedra Metodología de Sistemas II.

## Arquitectura y Estándares de Producción
* **Lenguaje**: Python 3.10+
* **Tipado Estricto**: Implementación integral de `typing` (`Protocol`, `Union`, `Tuple`, `Optional`) para validación estática de Pylance/MyPy.
* **Diseño Orientado a Dominio**: Entidades inmutables (`@dataclass(frozen=True)`), Parameter Objects (DTOs) y manejo de excepciones personalizadas (`SolicitudError`).
* **Inversión de Dependencias (DIP)**: Capa de persistencia aislada mediante el contrato `SolicitudRepositoryProtocol`, posibilitando el intercambio de JSON a motores SQL sin alterar la lógica de negocio.
* **Testing Automatizado**: Suite de verificación y validación con `pytest`, garantizando aislamiento de estado mediante *fixtures* temporales.

## Despliegue Local y Ejecución

1. Clonar el repositorio e inicializar el entorno virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install pytest