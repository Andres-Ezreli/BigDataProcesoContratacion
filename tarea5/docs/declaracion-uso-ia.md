# Declaración de uso de asistentes de inteligencia artificial

**Tarea T5 · Sesión 5 · Equipo [[COMPLETAR]]**

## Qué se usó y para qué

| Uso | Herramienta | Verificación realizada |
|---|---|---|
| Estructura del repositorio y de los scripts de ingesta | [[COMPLETAR]] | Revisión del equipo contra los seis criterios de aceptación del enunciado |
| Implementación de `cargar_cruda.py`, `demostrar_versionado.py` y `verificar_lago.py` | [[COMPLETAR]] | Ejecutados de principio a fin contra el MinIO del equipo; `verificar_lago.py` devuelve código de salida 0 |
| Redacción de la convención de rutas y del mapa de las tres capas | [[COMPLETAR]] | Sometida a la **prueba del tercero** (sección 2.5 de `T5_lago.md`): un integrante ajeno al código predijo la ruta de un objeto sin consultar a nadie |
| Redacción del informe | [[COMPLETAR]] | Reescrito por el equipo; la justificación de la partición y de la regla de inmutabilidad son propias |

## Qué no se delegó

- La elección de la fuente del proyecto y su continuidad desde T1.
- La decisión de particionar la capa cruda por **fecha de ingesta** y no por fecha del negocio, y el argumento de por qué la segunda opción obligaría a violar la inmutabilidad.
- La decisión de usar un cubo por capa en vez de un prefijo por capa, y el hecho de que la razón decisiva sea que el versionado se configura por cubo.
- La ejecución real contra MinIO y la captura de los `VersionId`.
- La interpretación de qué protege el versionado y qué no.
- La lista de límites de la sección 11 del informe: lo que este lago todavía no tiene.

## Verificación

Ninguna cifra ni ningún identificador del informe se transcribió de un asistente. Todo lo que aparece —claves de objeto, `sha256`, `VersionId`, número de filas y de columnas, tamaños— se genera ejecutando los scripts contra el almacenamiento del equipo y queda escrito en `docs/evidencia_ingesta.json`, `docs/evidencia_versionado.json`, `docs/evidencia_versionado.md`, `docs/evidencia_lago.json` y `docs/evidencia_lago.md`. Esos cinco archivos son generados: se regeneran en cada corrida y no se editan a mano.

El cumplimiento de los seis criterios de aceptación no se declara: lo comprueba `src/ingesta/verificar_lago.py` releyendo el lago, y su código de salida es 0 o 1.

Firman: [[COMPLETAR: los tres integrantes]]
