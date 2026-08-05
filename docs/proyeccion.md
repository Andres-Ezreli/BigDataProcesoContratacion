# Proyección de almacenamiento y factor de réplica

**Tarea acumulativa T3 · Sesión 3 · Módulo 1**
IFPN0025 · Big Data e Ingeniería de Datos · Universidad Ean

| | |
|---|---|
| Equipo | [[COMPLETAR: integrante 1, integrante 2, integrante 3]] |
| Repositorio | [[COMPLETAR: URL del repositorio consolidado]] |
| Commit | [[COMPLETAR: identificador del último commit]] |
| Fecha | 2026-08-04 (fecha de ejecución de la proyección; ajústenla si entregan otro día) |

---

## 1. Paso cero — consolidación de la fuente

De las tres fuentes medidas en las fichas T1, la elegida es **SECOP II — Procesos de Contratación** (portal `datos.gov.co`, conjunto `p6dx-8zbt`).

**Por qué esa y no las otras dos.** El criterio decisivo no fue el volumen: SECOP II (8,6435 GiB proyectados) e IDEAM (8,119 GiB) son de tamaño comparable, y las dos habrían dado una decisión de réplica igualmente real. Lo que las separa es si la proyección se puede *sostener con evidencia*.

- *Tasa de crecimiento observable* — **este es el criterio que decide.** SECOP II publica el conteo de filas por año, así que la `g` de esta proyección se mide sobre una serie real (1.531.557 filas en 2023 → 1.934.805 en 2025) en lugar de suponerse. Es la única de las tres cuya tasa de crecimiento no es un supuesto.
- *Formato de ingesta* — CSV UTF-8 plano de 59 columnas, servido por la API de Socrata. Se lee con un solo `read_csv` sin parsers a medida, y la descarga paginada con `$order=:id` es determinista: dos personas que ejecuten el mismo código obtienen exactamente las mismas filas. Eso reduce el riesgo de ingesta para T5 y es lo que hace posible la prueba del tercero de la sección 5.
- *Volumen suficiente* — 8,6435 GiB medidos exigen 26,7 GB de RAM para un `read_csv` completo, muy por encima de lo que admite un portátil de 16 GB. La decisión de réplica es real, no un ejercicio.
- *Licencia* — Datos Abiertos de Colombia, Ley 1712 de 2014, uso libre con atribución. **Advertencia de trazabilidad:** a diferencia de los otros tres criterios, este no se verificó contra el portal en T1 ni en T2. Es el único dato de la ficha sin evidencia medida y queda pendiente de confirmar antes de entregar.

**Las otras dos, y por qué se descartaron:**

- **IDEAM** se descartó porque su crecimiento **no es verificable**. La propia ficha T1 lo declara: no hay serie histórica de tamaño publicada, el volumen crece con el número de estaciones-sensor activas y no con el tiempo, y el 8 % anual que se usó allí está marcado como *«el número más débil del entregable»*. Además, la consulta agregada por año no termina contra el servidor del portal: el timeout es evidencia de volumen, pero no es una cifra con la que se pueda proyectar. Proyectar a doce meses sobre un supuesto no medible habría hecho que toda esta tarea descansara sobre una invención.
- **GEIH** se descartó por dos razones independientes. Primera, en T1 no se midió la fuente real sino un **sustituto sintético** (0,0086 GB), porque el DANE no expone API: hay que descargar un paquete, descomprimirlo y leer un diccionario de variables antes de poder leer los datos. Segunda, y más de fondo, **su acumulado crece de forma lineal, no geométrica**: el archivo de un periodo no crece, crece la colección de periodos. La fórmula `V₀ × (1 + g)ⁿ` sobreestimaría por construcción, y usarla habría sido aplicar el modelo equivocado sin decirlo.

Repositorio único del equipo: [[COMPLETAR: URL del repositorio consolidado]]. Las tres fichas T1 originales quedan archivadas en `docs/fichas-t1/` para trazabilidad.

---

## 2. Datos de entrada, fórmulas y resultados

Todos los números de esta sección salen de un único archivo de configuración, `src/fuente.json`, y se generan ejecutando:

```bash
python src/proyeccion.py
```

El script no tiene dependencias externas. Cualquier persona que clone el repositorio y ejecute esa línea obtiene exactamente estas cifras. La salida se escribe en `docs/tabla-proyeccion.md`.

### Fórmulas

| Qué calcula | Expresión |
|---|---|
| Volumen lógico a 12 meses | `V₁₂ = V₀ × (1 + g)¹²` |
| Almacenamiento físico | `S = V₁₂ × R` |
| Bloques por archivo | `ceil(tamaño_archivo / 128 MB)` |
| Tolerancia a fallos | `R − 1` nodos |

### Resultados

Salida literal de `python src/proyeccion.py`, reproducida también en `docs/tabla-proyeccion.md`.

#### Datos de entrada (ficha T1)

| Parámetro | Valor |
|---|---|
| Fuente | SECOP II — Procesos de Contratación (`datos.gov.co / p6dx-8zbt`) |
| Licencia | Datos Abiertos de Colombia — Ley 1712 de 2014, uso libre con atribución |
| Formato | CSV UTF-8 delimitado por comas, esquema plano, 59 columnas |
| Volumen actual (V₀) | 9,28 GB |
| Crecimiento mensual (g) | 0,98 % |
| Horizonte (n) | 12 meses |
| Archivo típico | 96 MB |
| Tamaño de bloque HDFS | 128 MB |
| Costo de almacenamiento | 0,023 USD por GB-mes |

#### Volumen lógico proyectado

V₁₂ = 9,28 × (1 + 0,009786)¹² = **10,43 GB** (factor de crecimiento: 1,1240×)

#### Almacenamiento físico por factor de réplica (a 12 meses)

| R | Almacenamiento físico | Sobrecosto vs R=1 | Nodos que puede perder | Costo mensual (USD) | Bloques físicos por archivo |
|---|---|---|---|---|---|
| 1 | 10,43 GB | +0,00 GB | 0 | 0,24 | 1 |
| 2 | 20,86 GB | +10,43 GB | 1 | 0,48 | 2 |
| 3 | 31,29 GB | +20,86 GB | 2 | 0,72 | 3 |

#### Bloques HDFS

`ceil(96,41 MB / 128 MB) = ` **1 bloque** por archivo. El archivo cabe en un solo bloque, que queda con 96,41 MB ocupados de 128 MB. HDFS no reserva el bloque completo en disco: el remanente no se desperdicia.

#### De dónde sale cada entrada

Ninguno de los cuatro valores de la ficha estaba escrito como tal en T1; dos son medidos y dos son deducidos. La trazabilidad completa está en los campos `_origen_*` de `src/fuente.json`.

| Entrada | Cómo se obtuvo |
|---|---|
| V₀ = 9,28 GB | **Deducido.** Muestra real de 200.000 filas = 0,194714 GiB en disco (T1, `secop_sample.csv`), escalada por 8.878.158 / 200.000 = 44,39079. El total de filas es `count(*)` contra la API de Socrata, verificado el 2026-07-24. Equivale a 8,6435 GiB. |
| g = 0,9786 % mensual | **Deducido.** CAGR anual 2023→2025 de la serie real de filas del portal: 1.531.557 → 1.934.805 en dos años = 12,3963 % anual; el mensual es (1 + 0,123963)^(1/12) − 1. Se excluyen 2021-2022 porque reflejan la migración de SECOP I a SECOP II, no crecimiento orgánico de la contratación. |
| Archivo típico 96,41 MB | Escenario de partición mensual: es el incremento del mes 12, el mayor de los doce (el del mes 1 es 86,62 MB). |
| Costo 0,023 USD/GB-mes | Precio de referencia de almacenamiento en nube usado en la consolidación del equipo. |

> **Nota de unidades.** T1 calculó los tamaños con `getsize / 1024**3` — es decir GiB — pero etiquetó los campos como `_gb`. Aquí se usan GB decimales, que es como se factura el almacenamiento. Por eso V₀ aparece como 9,28 GB y no como los 8,64 GiB de la ficha original: es la misma medición en otra unidad, no otra medición.

### Verificación a mano

El enunciado exige verificar cada cifra manualmente. Reconstrucción de la fila R = 3 con las cifras reales del equipo, paso a paso:

1. **El factor de crecimiento.** `1,009786¹² = 1,1239633302`. Se obtiene con doce multiplicaciones sucesivas de 1,009786, o como `1.009786^12` en calculadora. Comprobación cruzada: este factor debe devolver el crecimiento anual del que se derivó, y en efecto `1,1239633 − 1 = 12,3963 %`, que es el CAGR 2023→2025 de la serie del portal. Si estos dos números no coincidieran, el paso de anual a mensual estaría mal.
2. **Volumen lógico a doce meses.** `9,2809 GB × 1,1239633302 = 10,4313912714 GB` → **10,43 GB**.
3. **Almacenamiento físico con tres copias.** `10,4313912714 × 3 = 31,2941738143 GB` → **31,29 GB**.
4. **Sobrecosto en disco frente a R = 1.** `31,2941738143 − 10,4313912714 = 20,8627825429 GB` → **+20,86 GB**.
5. **Costo mensual.** `31,2941738143 × 0,023 USD = 0,7197659977` → **0,72 USD al mes**, es decir `0,72 × 12 = 8,64 USD al año`.
6. **Bloques.** `96,41 / 128 = 0,7532…` → se redondea hacia arriba: **1 bloque** por archivo mensual. Con R = 3: `1 × 3 = 3` bloques físicos por archivo.

**Comprobación independiente contra la consolidación previa del equipo.** El mismo cálculo hecho en unidades binarias tiene que dar el mismo resultado. Partiendo de V₀ = 8,6435 GiB: `8,6435 × 1,1239633302 = 9,7150 GiB`, y `9,7150 × 3 = 29,1450 GiB`. Convertido a decimal, `29,1450 GiB × 1,073741824 = 31,2942 GB`, que coincide con el paso 3 hasta la cuarta cifra decimal. Las dos rutas —decimal y binaria— llegan al mismo número, así que la diferencia entre 8,64 y 9,28 es de unidad y no de aritmética.

**Comprobación del costo anual.** `10,4313912714 GB × 0,023 USD × 12 meses = 2,879 USD` a R = 1, que redondea a los 2,88 USD/año esperados. La tercera réplica cuesta exactamente lo mismo que la primera: `2,88 USD al año`.

Todo coincide con la salida del script.

---

## 3. Recomendación de factor de réplica

> ⚠️ **PROPUESTA — PENDIENTE DE CONFIRMACIÓN DEL EQUIPO.** Toda esta sección es un borrador argumentado, no una decisión tomada. Léanla, discútanla y borren este aviso cuando la confirmen o la cambien.

**Factor propuesto: R = 3 en la zona cruda (`/raw`) y R = 2 en la derivada (`/derived`).**

### El compromiso, en una frase

Cada copia adicional compra un nodo más de tolerancia y cuesta un 100 % adicional del volumen lógico. Pasar de R=1 a R=2 compra la diferencia entre *perder el dato* y *no perderlo*: es la copia más barata que existe en términos de valor por gigabyte. Pasar de R=2 a R=3 compra tolerancia a la **falla simultánea** de dos nodos, un escenario mucho menos frecuente, al mismo precio. Por eso la segunda copia casi nunca se discute y la tercera sí.

### Criterio: dato crítico frente a dato regenerable

La pregunta que decide el factor no es "¿cuánto cuesta?" sino **"si perdemos esto, ¿podemos recuperarlo?"**

| Tipo de dato | ¿Regenerable? | Factor apropiado |
|---|---|---|
| Ingesta cruda desde una fuente pública que sigue en línea | Sí — se vuelve a descargar | R = 2 |
| Ingesta cruda de un origen que sobrescribe o expira | No — la ventana se cierra | R = 3 |
| Tablas derivadas y agregados | Sí — se recalculan desde la cruda | R = 2, incluso R = 1 en staging |
| Resultados que alimentan una decisión o entrega | No en tiempo razonable | R = 3 |

**Nuestro caso — y por qué no cabe en ninguna de las dos filas de arriba.**

La tabla ofrece una dicotomía: histórico permanente que se vuelve a descargar, o ventana móvil que se sobrescribe. **SECOP II no es ninguna de las dos**, y decirlo es la parte importante de este argumento.

*No es una ventana móvil.* El conjunto contiene la serie completa desde 2015 hasta hoy —los conteos anuales de la ficha T1 van de 5.528 registros en 2015 a 1.934.805 en 2025— y la API de Socrata permite paginarlo entero de forma determinista. El filtrado por ventana temporal con `$where` se usó en T1 para IDEAM, no para SECOP. **Si mañana se borra el clúster, la fuente se puede volver a bajar completa.** En ese sentido literal, es dato regenerable y R = 2 bastaría.

*Pero muta en sitio.* Los registros de SECOP II cambian de estado a medida que avanza cada proceso de contratación, y el portal **no conserva el estado anterior**. La evidencia está en la propia ficha T1: `fecha_de_publicacion_fase` viene nula en 8.811.110 de 8.878.158 filas, y se midieron 3.226 filas duplicadas completas y 6.972 duplicados de clave sobre una muestra de 200.000. Volver a descargar dentro de un mes no devuelve el conjunto que teníamos: devuelve otro, con las mismas filas en estados distintos y con filas nuevas intercaladas.

*La consecuencia, que es lo que decide el factor.* Lo irrecuperable no es la fuente, es **el snapshot**. Toda la cadena T1 → T2 → T3 está anclada a un corte concreto: `count(*) = 8.878.158` verificado el 2026-07-24. Ese conteo es el que produce V₀, y V₀ es el que produce todas las cifras de la sección 2. Si perdemos esa copia, no perdemos «unos datos que se vuelven a bajar»: perdemos la capacidad de reproducir la entrega, porque la descarga de hoy da un número distinto y ninguna cifra de este documento vuelve a cuadrar. La prueba del tercero de la sección 5 dejaría de pasar.

Por eso proponemos **R = 3 sobre `/raw`**: no porque el dato sea imposible de recuperar, sino porque *ese* estado del dato sí lo es, y es el estado sobre el que descansa la trazabilidad de todo el módulo. La zona derivada baja a **R = 2** porque sí se regenera: basta reejecutar `src/proyeccion.py` sobre la cruda.

### Alternativas consideradas

- **Réplica escalonada por zona.** No es obligatorio un único factor para todo el clúster: HDFS permite fijar el factor por directorio (`hdfs dfs -setrep`). La configuración que recomendamos es R=3 sobre `/raw` y R=2 sobre `/derived`, lo que baja el costo total sin tocar la durabilidad de lo que no se puede regenerar.
- **Erasure coding** (disponible desde Hadoop 3). Con un esquema RS(6,3) se obtiene una durabilidad comparable a R=3 con una sobrecarga de aproximadamente 1,5× en lugar de 3×. El costo se paga en CPU durante la reconstrucción y en latencia de lectura degradada, así que sirve para datos fríos y no para lo que se lee en caliente. Para nuestro volumen (10,43 GB a doce meses) el ahorro absoluto sería de unos 15,6 GB, es decir alrededor de 4,3 USD al año: no compensa la complejidad operativa. La conclusión cambiaría a escala de decenas de TB.
- **R = 1.** Descartado. No es una configuración de producción: la caída de un solo nodo implica pérdida definitiva y bloques corruptos que HDFS no puede reconstruir.

### Argumento ante quien paga la factura

Con R = 3, el gasto adicional frente a R = 1 es de **20,86 GB**, es decir **0,48 USD al mes** — **5,76 USD al año**. Ese monto compra la garantía de que la caída simultánea de **2** nodos no detiene el pipeline ni obliga a una reingesta.

Conviene desglosarlo, porque la discusión real no es R=1 contra R=3 sino **R=2 contra R=3**. La segunda copia es la que separa *perder el dato* de *no perderlo* y no se discute. La tercera copia, ella sola, cuesta **10,43 GB adicionales = 2,88 USD al año**: menos de veinticinco centavos de dólar al mes.

Puesto así, el argumento ante quien firma no necesita estimar horas-persona. Basta con la asimetría: la tercera réplica cuesta **2,88 USD al año**, y lo que compra es que el corte del 2026-07-24 —del que dependen las cifras de este documento y la reproducibilidad de todo el módulo— siga existiendo. Como se explicó arriba, ese corte **no se recupera reingiriendo**: el portal ya no lo tiene. Una reingesta devolvería datos, pero no *estos* datos, y con ellos se caería la prueba del tercero. Es un gasto de tres dólares al año contra un riesgo que ningún presupuesto posterior puede revertir.

*Cuándo dejaría de ser cierto:* si el volumen creciera unas 35 veces —hasta unos 362 GB lógicos—, la tercera réplica pasaría de 2,88 a más de 100 USD al año y valdría la pena reabrir la comparación con erasure coding. Al ritmo medido de 12,4 % anual eso está a décadas de distancia; no es una decisión que este equipo tenga que tomar hoy.

---

## 4. Componente en inglés

- Párrafo de síntesis: `docs/replication-summary-en.md`
- Términos nuevos: `docs/glosario-bilingue.md`

---

## 5. Reproducibilidad — prueba del tercero

Para que otra persona llegue a estas mismas cifras solo necesita:

1. Clonar el repositorio.
2. Abrir `src/fuente.json` y verificar que los valores coinciden con la ficha T1 del equipo.
3. Ejecutar `python src/proyeccion.py`.

No hay valores escritos a mano dentro del cálculo, no hay hojas de cálculo con celdas ocultas y no hay pasos manuales entre la entrada y la tabla. Las fórmulas están en `src/proyeccion.py`, una función por fórmula, con el nombre de la fórmula del enunciado.

---

## 6. Declaración de uso de asistentes de IA

Ver `docs/declaracion-uso-ia.md`.

---

## 7. Referencias

Kleppmann, M. (2017). *Designing data-intensive applications*. O'Reilly Media.

Shvachko, K., Kuang, H., Radia, S., y Chansler, R. (2010). The Hadoop Distributed File System. *2010 IEEE 26th Symposium on Mass Storage Systems and Technologies (MSST)*, 1-10. https://doi.org/10.1109/MSST.2010.5496972

White, T. (2015). *Hadoop: The definitive guide* (4.ª ed.). O'Reilly Media.
