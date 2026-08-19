<!-- Generado por src/mezcla/estimar.py. No editar a mano: vuelvan a ejecutarlo. -->

## Parametros de la medicion

| Parametro | Valor | Origen |
|---|---|---|
| Registros validos (N) | 20.000 | `docs/perfil.json` |
| Registros descartados | 1 | encabezado y filas sin valor numerico |
| Claves distintas (K) | 20 | `docs/perfil.json` |
| Mappers (M) | 1 | estimado por bloques |
| Reductores (R) | 3 | `esquema.json` / medicion |
| Bytes de clave, promedio | 10.0 B | medido |
| Bytes de valor del map, promedio | 12.9 B | medido, incluye `\t1` |
| Sobrecarga por par | 2 B | `esquema.json` |

## Estimacion contra medicion

| Escenario | Pares en la mezcla | Bytes estimados | Reduce shuffle bytes real | Error |
|---|---|---|---|---|
| Sin combinador | 20.000 | 485.7 KB | pendiente | pendiente |
| Con combinador, cota superior | 20 | 610 B | — | — |
| Con combinador, esperado | 20 | 610 B | pendiente | pendiente |

**Ahorro estimado del combinador:** 99.9 % de los bytes de mezcla (610 B frente a 485.7 KB).

**Ahorro medido:** pendiente. Peguen `reduce_shuffle_bytes` de las dos ejecuciones en `src/mezcla/medicion.json` y vuelvan a ejecutar este script.

> **Aviso.** El calculo asume 1 mapper. Con un solo mapper el combinador agrega todo el dato de una vez y el ahorro sale maximo, pero no dice nada sobre el comportamiento distribuido. Para que la comparacion sea significativa, la entrada debe ocupar varios bloques o hay que forzar mas splits (ver `docs/T4_ejecucion.md`, seccion 4).

## Sesgo de la clave

| Indicador | Valor |
|---|---|
| Clave mas frecuente | `BOGOTA D.C.` |
| Su participacion | 33.7 % de los registros |
| Participacion de las tres mayores | 62.4 % |
| Registros por clave, promedio | 1000.0 |
| Razon entre la mayor y el promedio | 6.7x |
| Carga del reductor mas cargado (R=3) | 10.893 registros |
| Carga ideal por reductor | 6.667 registros |
| Desbalance | 1.63x la carga ideal |

### Rediseno propuesto: clave compuesta con 7 cubos

La clave pasa de `BOGOTA D.C.` a `clave#b` con `b = hash(registro) % 7`, y un segundo trabajo vuelve a agregar por el prefijo.

| Indicador | Clave actual | Clave compuesta |
|---|---|---|
| Pares en la mezcla, con combinador | 20 | 140 |
| Bytes de mezcla estimados | 610 B | 4.3 KB |
| Reductor mas cargado | 10.893 | 7.455 |
| Desbalance | 1.63x | 1.12x |

El compromiso queda a la vista: el reductor mas cargado baja 32 %, pero la mezcla sube 621 % y aparece una segunda etapa que antes no existia.

### Las diez claves mas pesadas

| # | Clave | Registros | % del total | Pares con combinador (esperados) |
|---|---|---|---|---|
| 1 | `BOGOTA D.C.` | 6.738 | 33.69 % | 1.0 |
| 2 | `ANTIOQUIA` | 3.618 | 18.09 % | 1.0 |
| 3 | `VALLE DEL CAUCA` | 2.129 | 10.64 % | 1.0 |
| 4 | `CUNDINAMARCA` | 1.624 | 8.12 % | 1.0 |
| 5 | `SANTANDER` | 1.173 | 5.87 % | 1.0 |
| 6 | `ATLANTICO` | 1.006 | 5.03 % | 1.0 |
| 7 | `BOLIVAR` | 603 | 3.02 % | 1.0 |
| 8 | `NARINO` | 598 | 2.99 % | 1.0 |
| 9 | `TOLIMA` | 420 | 2.10 % | 1.0 |
| 10 | `HUILA` | 397 | 1.99 % | 1.0 |
