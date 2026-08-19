# Historial del lago

<!-- GENERADO por src/ingesta/historial_lago.py. No editar a mano.
     Se regenera en cada corrida. -->

Generado: `2026-08-19T17:45:43.467850+00:00` (UTC)

Este archivo es el equivalente escrito de la captura de pantalla de la
consola de MinIO. Una captura muestra un instante; esto muestra **todo lo
que le ha pasado a cada objeto**, con los `VersionId` reales que asigno el
almacenamiento. Se puede contrastar contra la consola web abriendo
<http://localhost:9001> y mirando el historial de versiones de cualquier
clave: los identificadores tienen que ser los mismos.

## Resumen

| Capa | Cubo | Versionado | Claves | Eventos | Bytes |
|---|---|---|---|---|---|
| cruda | `lago-cruda` | **activo** | 4 | 5 | 54.7 MiB |
| refinada | `lago-refinada` | no | 1 | 1 | 1.1 KiB |
| curada | `lago-curada` | no | 1 | 1 | 919.0 B |

## Línea de tiempo

Todo lo que ha ocurrido en el lago, en orden. Cada fila es una escritura
o un borrado. Nada se ha editado: en un almacen de objetos versionado no
existe la operacion *modificar*, solo *escribir una version nueva*.

| # | Instante (UTC) | Cubo | Clave | Qué pasó | VersionId | Bytes |
|---|---|---|---|---|---|---|
| 1 | `2026-08-19T17:26:49` | `lago-cruda` | `_LEEME.txt` | escritura | `244630f4-f155-...` | 2.3 KiB |
| 2 | `2026-08-19T17:26:49` | `lago-refinada` | `_LEEME.txt` | escritura | `(sin version)` | 1.1 KiB |
| 3 | `2026-08-19T17:26:49` | `lago-curada` | `_LEEME.txt` | escritura | `(sin version)` | 919.0 B |
| 4 | `2026-08-19T17:27:59` | `lago-cruda` | `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv` | escritura | `fd8636ab-2804-...` | 54.7 MiB |
| 5 | `2026-08-19T17:27:59` | `lago-cruda` | `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv.manifiesto.json` | escritura | `229f29ea-b880-...` | 3.6 KiB |
| 6 | `2026-08-19T17:28:00` | `lago-cruda` | `_evidencia/prueba-de-versionado.txt` | escritura | `2dd9f646-4801-...` | 429.0 B |
| 7 | `2026-08-19T17:28:00` | `lago-cruda` | `_evidencia/prueba-de-versionado.txt` | escritura | `9be35f41-0860-...` | 436.0 B |

## Historial objeto por objeto

### `lago-cruda`

#### `_LEEME.txt`

documentacion del cubo · **1 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `244630f4-f155-414d-8c60-9591d12f32ab` | **sí** | escritura | 2.3 KiB | `2026-08-19T17:26:49` | — |

#### `_evidencia/prueba-de-versionado.txt`

sonda de la prueba de versionado · **2 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `9be35f41-0860-43ef-a8f3-0d7fe22ddf76` | **sí** | escritura | 436.0 B | `2026-08-19T17:28:00` | — |
| `2dd9f646-4801-4899-9a1f-d13f8ecf26ff` | no | escritura | 429.0 B | `2026-08-19T17:28:00` | — |

> Esta clave se escribió más de una vez. La versión anterior
> sigue siendo recuperable con `GetObject` indicando su
> `VersionId`: eso es lo que demuestra el criterio 3.

#### `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv`

DATO del proyecto · **1 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `fd8636ab-2804-4d9d-a62d-37ef9a7f2b0c` | **sí** | escritura | 54.7 MiB | `2026-08-19T17:27:59` | `37b3b013f61e6b71…` |

#### `secop2_procesos/anio=2026/mes=08/dia=19/secop2_procesos_20260819.csv.manifiesto.json`

manifiesto (ficha tecnica) · **1 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `229f29ea-b880-4065-8eb2-fb0e014e0fcc` | **sí** | escritura | 3.6 KiB | `2026-08-19T17:27:59` | — |

### `lago-refinada`

#### `_LEEME.txt`

documentacion del cubo · **1 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `null` | **sí** | escritura | 1.1 KiB | `2026-08-19T17:26:49` | — |

### `lago-curada`

#### `_LEEME.txt`

documentacion del cubo · **1 versión(es)**

| VersionId | ¿Actual? | Qué es | Bytes | Instante (UTC) | sha256 |
|---|---|---|---|---|---|
| `null` | **sí** | escritura | 919.0 B | `2026-08-19T17:26:49` | — |

## Cómo leer esto

- **El dato del proyecto tiene una sola versión.** Si alguna clave
  marcada como *DATO del proyecto* apareciera con dos, alguien habría
  sobrescrito la capa cruda y la regla de inmutabilidad estaría rota.
- **La sonda sí tiene varias**, y es a propósito: existe únicamente para
  demostrar que sobrescribir no pierde nada.
- **Un marcador de borrado no borra.** Oculta la clave y deja el
  contenido accesible por `VersionId`.

## Cómo reproducirlo

```bash
python3 src/ingesta/historial_lago.py
```
