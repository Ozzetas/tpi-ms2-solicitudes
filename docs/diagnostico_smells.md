# Diagnóstico de Deuda Técnica y Code Smells (Etapa 3)

Análisis estructural realizado sobre el módulo monolítico inicial `sistema_solicitudes.py`.

## Matriz de Hallazgos

| ID | Code Smell | Ubicación | Riesgo | Prioridad |
| :--- | :--- | :--- | :--- | :--- |
| CS-01 | Long Method / God Function | Función `procesar_sistema` | Muy Alto | Crítica |
| CS-02 | Long Parameter List | Firma `procesar_sistema` (14 params) | Alto | Alta |
| CS-03 | Primitive Obsession | Diccionarios crudos y códigos enteros | Alto | Alta |
| CS-04 | Magic Numbers / Strings | Condicionales de acción, tipo y estado | Medio | Media |
| CS-05 | Duplicated Code | Apertura y volcado manual de JSON | Alto | Alta |
| CS-06 | Exception Swallowing | Bloques `except Exception: pass` (Mitigado en v1.1) | Muy Alto | Crítica |
| CS-07 | Global Mutable State | Lista global `solicitudes_memoria` | Alto | Alta |
| CS-08 | Divergent Change | Archivo `sistema_solicitudes.py` | Alto | Alta |

## Justificación Técnica del Impacto
1. **Acoplamiento de Responsabilidades**: La lógica de validación académica, el flujo de estados y la persistencia en disco residen en un mismo bloque procedural, violando el Principio de Responsabilidad Única (SRP).
2. **Inviabilidad de Pruebas Unitarias Aisladas**: El uso de estado mutable global y una ruta de archivo fija provoca contaminación de datos entre ejecuciones.
3. **Ausencia de Tipado y Contratos**: Al depender de un entero (`accion`) para determinar el comportamiento y el tipo de retorno de una única función, se destruye la previsibilidad del sistema y se anula la inferencia de tipos del IDE.