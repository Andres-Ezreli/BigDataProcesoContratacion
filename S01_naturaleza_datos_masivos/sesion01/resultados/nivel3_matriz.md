# Nivel 3 - Autonomo · Que V restringe primero, y por que las otras cuatro no

**IFPN0025 · Big Data e Ingenieria de Datos · Universidad Ean**  
**Sesion 1 · Practica S01_P4_v1 · Andres**  
Generado el 2026-07-24 18:54.

---

## 0. Regla de trabajo

Elegir la V dominante no cuesta nada. **El trabajo esta en descartar las otras cuatro**, y descartar exige haber mirado el dato. Por eso, antes de la matriz, este es el inventario de lo que efectivamente medi. Toda celda de la matriz apunta a una de estas mediciones o declara que no pudo hacerse.

## 1. Mediciones que hice para poder descartar

| Fuente | Nulos (media / max) | Cols >50% nulas | Filas duplicadas | Duplicados de clave | Cols de texto | Largo medio texto | Texto libre (>80 car.) |
|---|---|---|---|---|---|---|---|
| SECOP II | 12.8% / 100.0% | 8 | 1.61% | 3.5% | 44/59 | 25 car. | 3 |
| IDEAM | 0.0% / 0.0% | 0 | 0.00% | 99.9% | 7/12 | 15 car. | 0 |
| GEIH (sustituto sintetico) | 10.9% / 25.2% | 0 | 0.00% | n/a | 0/28 | n/a | 0 |

**Velocidad: frecuencia declarada contra frecuencia observada en las marcas de tiempo del propio archivo.**

| Fuente | Frecuencia declarada | Primer registro | Ultimo registro | Registros/hora observados | Latencia hasta hoy |
|---|---|---|---|---|---|
| SECOP II | continua / diaria | 2015-06-03 00:00 | 2026-07-23 00:00 | 2.0 | 2.0 dias |
| IDEAM | horaria por estacion, publicacion diaria | 2026-06-01 00:00 | 2026-06-10 23:58 | 833.5 | 44.0 dias |
| GEIH (sustituto sintetico) | — | — | — | — | sin columna temporal |

**Evidencia adicional consultada directamente contra la API del portal (2026-07-24), no contra la muestra:**

- `SELECT count(*)` sobre SECOP II `p6dx-8zbt` → **8,878,158 filas**.
- `count(*) GROUP BY date_extract_y(fecha_de_publicacion)` sobre el mismo conjunto → **8,811,110 filas (99.2%) tienen esa fecha vacia**. Ese numero es el hallazgo de veracidad mas fuerte del ejercicio.
- `count(*) WHERE fechaobservacion BETWEEN '2026-07-01' AND '2026-07-02'` sobre IDEAM `sbwg-7ju4` → **21,710 registros en 24 horas** ≈ 905 estaciones-sensor reportando cada hora.
- La ficha del conjunto de IDEAM declara literalmente que **los datos no han sido validados por el IDEAM**, que son *crudos instantaneos* de sensores y que *pueden presentar errores e inconsistencias, incluso fuera de los limites normales*. Es una fuente que documenta su propio problema de veracidad.
- La GEIH del DANE **no tiene API**. Para leerla hay que descargar un paquete, descomprimirlo y abrir primero un diccionario de variables que no es la GEIH. Esa dependencia documental es, en si misma, la medicion de variedad.

---

## 2. Matriz · 3 fuentes x 5 V

En la celda de la V dominante va la evidencia. En las otras cuatro va **la razon por la que esa V no restringe primero**.

| Fuente | Volumen | Velocidad | Variedad | Veracidad | Valor |
|---|---|---|---|---|---|
| **SECOP II** | **DOMINANTE.** 8,878,158 filas x 59 columnas. S0 proyectado 8.64 GB, k = 3.09 → **26.7 GB de RAM** para cargarla completa. Umbral con M de 16 GB: -8.1 anos. | No restringe: la publicacion es continua pero de bajo caudal. Observado en la muestra: 2 registros/hora, cuatro ordenes de magnitud por debajo de IDEAM. Nadie decide nada en esta fuente en menos de un dia. | No restringe, aunque es alta: 44/59 columnas de texto y 3 de texto libre largo. Es lo que **causa** el k alto, pero el esquema es unico, plano y estable entre periodos: se lee con un solo `read_csv`. La variedad encarece el volumen, no lo precede. | **Casi la desbanca.** 99% de las filas no tienen `fecha_de_publicacion`, y la muestra da 12.8% de nulos medios. No restringe **primero** porque el dato sucio sigue teniendo que caber en memoria antes de poder limpiarse: la veracidad es el problema del paso siguiente. | No restringe: el valor esta demostrado por uso. Es la fuente de referencia de control fiscal y de estudios de mercado publico; si desapareciera manana, se caerian decisiones de auditoria concretas. |
| **IDEAM** | No restringe primero: cada registro es estrecho (12 columnas, S0 muestra 0.0293 GB) y el filtro por ventana temporal en el servidor (`$where`) permite no traer nunca la serie completa. El volumen es grande pero **particionable por fecha sin perdida de sentido**. | **DOMINANTE.** 21,710 registros en 24 h medidos en el servidor ≈ 905 estaciones-sensor por hora. La consulta agregada por ano **no termina** contra el portal: el propio timeout es la medida. Y la asimetria clave: la frecuencia de **registro** es horaria pero la de **publicacion** declarada es diaria. Esa brecha, no el tamano, es lo que rompe cualquier caso de uso de alerta temprana. | No restringe: 12 columnas, esquema estrecho, estable y autoexplicativo; 0 columnas de texto libre largo. Un solo `read_csv` sin opciones basta. | No restringe primero, **pero es el segundo candidato serio y esta declarado por la propia fuente**: la ficha advierte que los datos son crudos, no validados, y pueden salirse de rangos normales. No restringe antes porque el control de calidad se aplica sobre la ventana que ya se trajo, y traer la ventana a tiempo es el problema previo. | No restringe: el valor es directo y verificable — alertas hidrometeorologicas y gestion de riesgo. Lo que si limita el valor es la latencia, y eso ya se conto como velocidad. |
| **GEIH (sustituto sintetico)** | No restringe: el universo util es **un periodo**, no la serie historica. Un mes de microdatos se maneja en un portatil sin dificultad (S0 medido 0.0086 GB, k = 1.93, umbral 218 anos). Nadie carga diez anos de GEIH a la vez porque las variables no son comparables entre ellos. | No restringe: publicacion mensual con rezago de semanas. Es la fuente mas lenta de las tres por un margen enorme, y esa lentitud es de diseno, no un defecto. | **DOMINANTE.** Es la unica de las tres en la que **hay que leer un documento que no son los datos antes de poder leer los datos**. Multiples archivos por descarga (vivienda, hogares, ocupados, desocupados, inactivos), sin API, con diccionario separado y con codigos de variable que cambian entre rediseños de la encuesta. En la muestra: 28 columnas y 0 de ellas con mas del 50 % de nulos — nulos que en su mayoria **no son ausencia de dato sino no-aplicabilidad de la pregunta**, y distinguir una cosa de la otra exige el diccionario. El costo aqui no es de RAM, es de interpretacion. | No restringe primero: nulos medios 10.9%, pero son en su mayoria estructurales y estan documentados. Un nulo documentado no es un problema de veracidad, es un problema de variedad — y por eso la variedad va primero. | No restringe: sostiene la medicion oficial de desempleo del pais. El valor es alto y no esta en discusion. |

---

## 3. Contraste con la hipotesis de la guia

La tabla de la seccion 2 de la guia propone Volumen / Velocidad / Variedad para SECOP II / IDEAM / GEIH. **Mi medicion la confirma en las tres**, pero con dos matices que solo aparecen al medir:

1. En SECOP II, **la veracidad casi desplaza al volumen**. Un 99% de nulos en una columna de fecha no es ruido, es un campo que en la practica no existe. Si el caso de uso fuera series temporales de contratacion, la veracidad seria la restriccion dominante y la tabla estaria equivocada para ese caso. El orden de las V **depende del uso**, no solo de la fuente.
2. En IDEAM, lo que restringe no es la frecuencia de registro sino **la brecha entre frecuencia de registro y frecuencia de publicacion**. Medir solo la primera habria dado una respuesta correcta por la razon equivocada.

---

## 4. Que no pude verificar, y por que

| No verificado | Por que | Que haria falta |
|---|---|---|
| Tamano historico total de IDEAM por ano | La consulta agregada `GROUP BY ano` no termina contra el servidor de Socrata. El timeout es evidencia de volumen pero no es una cifra. | Descarga por ventanas mensuales y suma local, o solicitud directa al IDEAM. |
| `k` de la GEIH real | No hay API; la descarga es manual desde `dane.gov.co/microdatos` y requiere descomprimir el paquete del periodo. | Ejecutar `ejecutar_todo.py` con el paquete ya descomprimido en `data/raw/geih/`. |
| Proporcion de nulos estructurales vs. nulos de captura en la GEIH | Exige cruzar cada columna con el diccionario de variables, columna por columna. | El diccionario del periodo y una tabla de aplicabilidad por pregunta. |
| Valor economico de cada fuente | El valor no se mide en el archivo, se mide en la organizacion. Lo argumente por uso documentado, no por medicion. | Entrevistas con quien consume cada fuente. |

---

## 5. Cierre · ¿que tuve que medir para poder descartar?

Para descartar **veracidad** medi la proporcion de nulos por columna, las columnas con mas del 50 % de vacios y los duplicados de clave; en SECOP II eso obligo a una consulta agregada contra el servidor porque la muestra no revelaba el problema. Para descartar **velocidad** compare la frecuencia declarada en la ficha del conjunto con la observada en las marcas de tiempo del archivo, y calcule la latencia hasta hoy. Para descartar **variedad** conte columnas de texto y medi el largo medio de cada una para separar texto categorico de texto libre. **Valor** es la unica que no medi en el archivo, porque no esta en el archivo: la argumente por uso documentado y lo declaro como tal. Lo que aprendi al descartar es que la V dominante no es una propiedad de la fuente sino de la pareja fuente-uso.

*(141 palabras aprox. en este cierre.)*